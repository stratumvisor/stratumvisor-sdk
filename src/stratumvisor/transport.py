"""HTTP transport for STRATUM."""
from __future__ import annotations

import json as jsonlib
import mimetypes
import os
import re
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Mapping, MutableMapping, Optional, Tuple, Union
from urllib.parse import urljoin, urlsplit, unquote

import requests
from requests import Response, Session
from requests.adapters import HTTPAdapter
from requests.auth import AuthBase, HTTPBasicAuth
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import SSLError, Timeout
from urllib3.util.retry import Retry

from .exceptions import (
    StratumAPIError,
    StratumAuthenticationError,
    StratumAuthorizationError,
    StratumConflictError,
    StratumConnectionError,
    StratumNotFoundError,
    StratumTLSException,
    StratumTimeoutError,
    StratumValidationError,
    error_code_from_payload,
)

TimeoutValue = Union[float, Tuple[float, Optional[float]]]
ProgressCallback = Callable[[int, Optional[int]], None]
VerifyValue = Union[bool, str, os.PathLike]
CertValue = Union[str, os.PathLike, Tuple[Union[str, os.PathLike], Union[str, os.PathLike]]]

_TRUST_HEADERS = {
    "remote-user",
    "remote-groups",
    "remote-name",
    "remote-email",
    "x-auth-proxy-secret",
}


class _ProgressReader:
    def __init__(self, fileobj: Any, total: int, callback: Optional[ProgressCallback]) -> None:
        self.fileobj = fileobj
        self.total = total
        self.callback = callback
        self.sent = 0

    def read(self, size: int = -1) -> bytes:
        chunk = self.fileobj.read(size)
        if chunk:
            self.sent += len(chunk)
            if self.callback:
                self.callback(self.sent, self.total)
        return chunk

    def __getattr__(self, name: str) -> Any:
        return getattr(self.fileobj, name)




class _MultipartStream:
    """Small streaming multipart/form-data encoder with a known Content-Length."""

    def __init__(self, fields: Mapping[str, Any], file_fields: Mapping[str, Any], progress: Optional[ProgressCallback]) -> None:
        self.boundary = "----stratumvisor-" + uuid.uuid4().hex
        self.content_type = f"multipart/form-data; boundary={self.boundary}"
        self._parts: list[Any] = []
        self._offset = 0
        self._index = 0
        self._opened: list[Any] = []
        self._progress = progress
        self._read_total = 0

        def q(value: Any) -> str:
            return str(value).replace("\\", "\\\\").replace('"', '\\"')

        for name, value in fields.items():
            if value is None:
                continue
            prefix = (
                f"--{self.boundary}\r\n"
                f"Content-Disposition: form-data; name=\"{q(name)}\"\r\n\r\n"
                f"{value}\r\n"
            ).encode("utf-8")
            self._parts.append(prefix)

        for field_name, value in file_fields.items():
            if isinstance(value, tuple):
                filename, source, ctype = value
            else:
                source = value
                filename = Path(source).name
                ctype = None
            fp = open(source, "rb")
            self._opened.append(fp)
            ctype = ctype or mimetypes.guess_type(str(filename))[0] or "application/octet-stream"
            prefix = (
                f"--{self.boundary}\r\n"
                f"Content-Disposition: form-data; name=\"{q(field_name)}\"; filename=\"{q(filename)}\"\r\n"
                f"Content-Type: {ctype}\r\n\r\n"
            ).encode("utf-8")
            self._parts.extend([prefix, fp, b"\r\n"])

        self._parts.append(f"--{self.boundary}--\r\n".encode("ascii"))
        self.len = 0
        for part in self._parts:
            if isinstance(part, (bytes, bytearray)):
                self.len += len(part)
            else:
                self.len += os.fstat(part.fileno()).st_size

    def read(self, size: int = -1) -> bytes:
        if size == 0:
            return b""
        want = None if size is None or size < 0 else size
        chunks: list[bytes] = []
        got = 0
        while self._index < len(self._parts) and (want is None or got < want):
            part = self._parts[self._index]
            remaining = -1 if want is None else want - got
            if isinstance(part, (bytes, bytearray)):
                blob = bytes(part)
                if self._offset >= len(blob):
                    self._index += 1
                    self._offset = 0
                    continue
                end = len(blob) if remaining < 0 else min(len(blob), self._offset + remaining)
                chunk = blob[self._offset:end]
                self._offset = end
                if self._offset >= len(blob):
                    self._index += 1
                    self._offset = 0
            else:
                chunk = part.read(remaining)
                if not chunk:
                    self._index += 1
                    self._offset = 0
                    continue
            chunks.append(chunk)
            got += len(chunk)
        out = b"".join(chunks)
        if out:
            self._read_total += len(out)
            if self._progress:
                self._progress(self._read_total, self.len)
        return out

    def close(self) -> None:
        for fp in self._opened:
            try:
                fp.close()
            except Exception:
                pass
        self._opened.clear()

class Transport:
    """Synchronous HTTP transport."""

    def __init__(
        self,
        base_url: str,
        *,
        username: Optional[str] = None,
        password: Optional[str] = None,
        token: Optional[str] = None,
        cookies: Optional[Mapping[str, str]] = None,
        auth: Optional[AuthBase] = None,
        verify: VerifyValue = True,
        cert: Optional[CertValue] = None,
        timeout: TimeoutValue = (10.0, 60.0),
        transfer_timeout: TimeoutValue = (30.0, None),
        retry_reads: int = 2,
        user_agent: str = "stratumvisor-sdk/0.3.0",
        session: Optional[Session] = None,
    ) -> None:
        if not base_url or not base_url.strip():
            raise ValueError("base_url is required")
        parsed_base = urlsplit(base_url)
        if (parsed_base.scheme.lower() != "https" or not parsed_base.hostname
                or parsed_base.username is not None or parsed_base.password is not None
                or parsed_base.query or parsed_base.fragment):
            raise ValueError("base_url must be an HTTPS URL without embedded credentials or query")
        self.base_url = base_url.rstrip("/") + "/"
        self._origin = (parsed_base.scheme.lower(), parsed_base.hostname.lower(), parsed_base.port or 443)
        self.verify = str(verify) if isinstance(verify, os.PathLike) else verify
        if self.verify is False:
            raise ValueError("TLS certificate verification is required")
        if isinstance(cert, tuple):
            self.cert = tuple(str(x) for x in cert)
        elif isinstance(cert, os.PathLike):
            self.cert = str(cert)
        else:
            self.cert = cert
        self.timeout = timeout
        self.transfer_timeout = transfer_timeout
        self.session = session or requests.Session()
        self.session.headers.setdefault("Accept", "application/json")
        self.session.headers["User-Agent"] = user_agent

        selected = sum(bool(x) for x in (auth, token, username or password))
        if selected > 1:
            raise ValueError("choose one of auth, token, or username/password")
        if (username is None) ^ (password is None):
            raise ValueError("username and password must be supplied together")
        if auth is not None:
            self.session.auth = auth
        elif username is not None and password is not None:
            self.session.auth = HTTPBasicAuth(username, password)
        elif token:
            self.session.headers["Authorization"] = f"Bearer {token}"
        if cookies:
            self.session.cookies.update(cookies)

        retry = Retry(
            total=max(0, int(retry_reads)),
            connect=max(0, int(retry_reads)),
            read=0,
            status=0,
            redirect=0,
            allowed_methods=frozenset({"GET", "HEAD", "OPTIONS"}),
            backoff_factor=0.25,
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def close(self) -> None:
        self.session.close()

    def _url(self, path: str) -> str:
        if not isinstance(path, str) or not path.startswith("/") or path.startswith("//"):
            raise ValueError("path must be a relative STRATUM API path beginning with /")
        parsed = urlsplit(path)
        if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
            raise ValueError("supply query arguments through params, not the path")
        segments = unquote(parsed.path).split("/")
        if any(segment in (".", "..") for segment in segments):
            raise ValueError("dot segments are not supported in API paths")
        url = urljoin(self.base_url, path.lstrip("/"))
        target = urlsplit(url)
        if ((target.scheme.lower(), (target.hostname or "").lower(), target.port or 443)
                != self._origin):
            raise ValueError("cross-origin requests are not permitted")
        return url

    def _check_headers(self, headers: Optional[Mapping[str, str]]) -> None:
        if not headers:
            return
        forbidden = sorted(k for k in headers if k.lower() in _TRUST_HEADERS)
        if forbidden:
            raise ValueError(
                "unsupported authentication header(s): "
                + ", ".join(forbidden)
            )

    def send(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json: Any = None,
        data: Any = None,
        files: Any = None,
        headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[TimeoutValue] = None,
        stream: bool = False,
        unwrap: bool = True,
        allow_redirects: bool = False,
    ) -> Any:
        if allow_redirects:
            raise ValueError("redirects are not supported")
        self._check_headers(self.session.headers)
        self._check_headers(headers)
        url = self._url(path)
        try:
            response = self.session.request(
                method.upper(),
                url,
                params=params,
                json=json,
                data=data,
                files=files,
                headers=dict(headers or {}),
                timeout=self.timeout if timeout is None else timeout,
                verify=self.verify,
                cert=self.cert,
                stream=stream,
                allow_redirects=allow_redirects,
            )
        except SSLError as exc:
            raise StratumTLSException(str(exc)) from exc
        except Timeout as exc:
            raise StratumTimeoutError(str(exc)) from exc
        except RequestsConnectionError as exc:
            raise StratumConnectionError(str(exc)) from exc

        self._raise_for_response(response, method=method, url=url)
        if stream:
            return response
        return self._decode_success(response, unwrap=unwrap)

    def _json_payload(self, response: Response) -> Any:
        try:
            return response.json()
        except ValueError:
            return None

    def _raise_for_response(self, response: Response, *, method: str, url: str) -> None:
        if 200 <= response.status_code < 300:
            return
        payload = self._json_payload(response)
        message = ("Authentication is required" if response.status_code in (301, 302, 303, 307, 308)
                   else "STRATUM API request failed")
        code = error_code_from_payload(payload, "")
        if code and not re.fullmatch(r"[A-Z][A-Z0-9_]{1,63}", code):
            code = None
        cls = StratumAPIError
        if response.status_code == 401 or response.status_code in (301, 302, 303, 307, 308):
            cls = StratumAuthenticationError
        elif response.status_code == 403:
            cls = StratumAuthorizationError
        elif response.status_code == 404:
            cls = StratumNotFoundError
        elif response.status_code == 409:
            cls = StratumConflictError
        elif response.status_code in (400, 413, 422):
            cls = StratumValidationError
        raise cls(
            message,
            status_code=response.status_code,
            code=code,
            method=method.upper(),
            url=url,
            details=None,
        )

    def _decode_success(self, response: Response, *, unwrap: bool) -> Any:
        if response.status_code == 204 or not response.content:
            return None
        ctype = response.headers.get("Content-Type", "").lower()
        if "json" not in ctype:
            return response.content
        payload = self._json_payload(response)
        if isinstance(payload, Mapping) and payload.get("ok") is False:
            raise StratumAPIError("STRATUM operation failed", status_code=response.status_code)
        if unwrap and isinstance(payload, Mapping) and payload.get("status") == "success" and "data" in payload:
            return payload.get("data")
        return payload

    def upload_stream(
        self,
        path: str,
        source: Union[str, os.PathLike],
        *,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
        content_type: Optional[str] = None,
        progress: Optional[ProgressCallback] = None,
        unwrap: bool = True,
    ) -> Any:
        source_path = Path(source)
        total = source_path.stat().st_size
        h = dict(headers or {})
        h.setdefault("Content-Type", content_type or mimetypes.guess_type(source_path.name)[0] or "application/octet-stream")
        h["Content-Length"] = str(total)
        with source_path.open("rb") as fileobj:
            reader = _ProgressReader(fileobj, total, progress)
            return self.send(
                "POST",
                path,
                params=params,
                data=reader,
                headers=h,
                timeout=self.transfer_timeout,
                unwrap=unwrap,
            )

    def multipart(
        self,
        method: str,
        path: str,
        *,
        fields: Mapping[str, Any],
        file_fields: Mapping[str, Union[str, os.PathLike, Tuple[str, Union[str, os.PathLike], Optional[str]]]],
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
        progress: Optional[ProgressCallback] = None,
        unwrap: bool = True,
    ) -> Any:
        encoder = _MultipartStream(fields, file_fields, progress)
        try:
            h = dict(headers or {})
            h["Content-Type"] = encoder.content_type
            h["Content-Length"] = str(encoder.len)
            return self.send(
                method,
                path,
                params=params,
                data=encoder,
                headers=h,
                timeout=self.transfer_timeout,
                unwrap=unwrap,
            )
        finally:
            encoder.close()

    def download(
        self,
        method: str,
        path: str,
        destination: Union[str, os.PathLike],
        *,
        params: Optional[Mapping[str, Any]] = None,
        json: Any = None,
        headers: Optional[Mapping[str, str]] = None,
        progress: Optional[ProgressCallback] = None,
        chunk_size: int = 1024 * 1024,
    ) -> Path:
        response = self.send(
            method,
            path,
            params=params,
            json=json,
            headers=headers,
            timeout=self.transfer_timeout,
            stream=True,
            unwrap=False,
        )
        dest = Path(destination)
        if dest.exists() and dest.is_dir():
            dest = dest / self._response_filename(response, fallback="stratum-download.bin")
        elif str(destination).endswith(("/", os.sep)):
            dest.mkdir(parents=True, exist_ok=True)
            dest = dest / self._response_filename(response, fallback="stratum-download.bin")
        dest.parent.mkdir(parents=True, exist_ok=True)
        import tempfile
        part_fd, part_path = tempfile.mkstemp(prefix="." + dest.name + ".", suffix=".part", dir=str(dest.parent))
        part = Path(part_path)
        total = response.headers.get("Content-Length")
        total_int = int(total) if total and total.isdigit() else None
        written = 0
        try:
            with os.fdopen(part_fd, "wb") as out:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if not chunk:
                        continue
                    out.write(chunk)
                    written += len(chunk)
                    if progress:
                        progress(written, total_int)
            os.replace(part, dest)
            return dest
        finally:
            response.close()
            if part.exists():
                try:
                    part.unlink()
                except OSError:
                    pass

    @staticmethod
    def _response_filename(response: Response, *, fallback: str) -> str:
        value = response.headers.get("Content-Disposition", "")
        match = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)', value, re.IGNORECASE)
        if match:
            return os.path.basename(match.group(1).strip())
        return fallback
