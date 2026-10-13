"""OpenAPI operation client."""
from __future__ import annotations

import json
from importlib.resources import files
from typing import Any, Dict, Iterable, Mapping, Optional
from urllib.parse import quote


class OpenAPIOperations:
    def __init__(self, client: Any) -> None:
        self._client = client
        resource = files("stratumvisor").joinpath("data/operations.json")
        self._operations: Dict[str, Dict[str, Any]] = json.loads(resource.read_text(encoding="utf-8"))

    def list(self) -> list[str]:
        return sorted(self._operations)

    def describe(self, operation_id: str) -> Dict[str, Any]:
        try:
            return dict(self._operations[operation_id])
        except KeyError as exc:
            raise KeyError(f"unknown STRATUM operationId: {operation_id}") from exc

    def call(
        self,
        operation_id: str,
        *,
        body: Any = None,
        parameters: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
        file_fields: Optional[Mapping[str, Any]] = None,
        data: Any = None,
        content_type: Optional[str] = None,
        stream: bool = False,
        unwrap: bool = True,
        **kwargs: Any,
    ) -> Any:
        """Invoke a public operation by its OpenAPI operation ID."""
        meta = self.describe(operation_id)
        supplied: Dict[str, Any] = dict(parameters or {})
        supplied.update(kwargs)
        query: Dict[str, Any] = {}
        call_headers: Dict[str, str] = dict(headers or {})
        path = meta["path"]

        for param in meta.get("parameters", []):
            name = param["name"]
            if name not in supplied:
                if param.get("required"):
                    raise TypeError(f"{operation_id} requires parameter {name!r}")
                continue
            value = supplied.pop(name)
            if value is None and not param.get("required"):
                continue
            where = param.get("in")
            if where == "query":
                query[name] = value
            elif where == "header":
                call_headers[name] = str(value)
            elif where == "path":
                path = path.replace("{" + name + "}", quote(str(value), safe=""))

        ctypes = list(meta.get("content_types") or [])
        selected = content_type
        if selected is None:
            if "application/json" in ctypes:
                selected = "application/json"
            elif "multipart/form-data" in ctypes:
                selected = "multipart/form-data"
            elif "application/octet-stream" in ctypes:
                selected = "application/octet-stream"
            elif ctypes:
                selected = ctypes[0]

        if selected == "application/json":
            if file_fields or data is not None:
                raise TypeError(f"{operation_id} expects a JSON request body")
            if body is None and supplied:
                body = supplied
                supplied = {}
            if supplied:
                raise TypeError(f"unused arguments for {operation_id}: {', '.join(sorted(supplied))}")
            if body is None and meta.get("request_body_required"):
                raise TypeError(f"{operation_id} requires a request body")
            return self._client.request(
                meta["method"], path, params=query, json=body, headers=call_headers,
                stream=stream, unwrap=unwrap,
            )

        if selected == "multipart/form-data":
            fields = dict(body or {})
            fields.update(supplied)
            return self._client.transport.multipart(
                meta["method"], path, params=query, headers=call_headers,
                fields=fields, file_fields=dict(file_fields or {}), unwrap=unwrap,
            )

        if selected == "application/octet-stream":
            if supplied:
                raise TypeError(f"unused arguments for {operation_id}: {', '.join(sorted(supplied))}")
            h = dict(call_headers)
            h.setdefault("Content-Type", selected)
            return self._client.request(
                meta["method"], path, params=query, data=data, headers=h,
                stream=stream, unwrap=unwrap,
            )

        if supplied:
            if meta["method"] in {"GET", "HEAD", "DELETE"}:
                query.update(supplied)
            else:
                raise TypeError(f"unused arguments for {operation_id}: {', '.join(sorted(supplied))}")
        return self._client.request(
            meta["method"], path, params=query, headers=call_headers,
            stream=stream, unwrap=unwrap,
        )
