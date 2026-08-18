"""Arsenal Forge, templates, media, and portable bundle APIs."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Sequence, Union
from urllib.parse import quote

from .exceptions import StratumNotFoundError
from .models import MediaItem, Template
from .transport import ProgressCallback


class ArsenalManager:
    def __init__(self, client: Any) -> None:
        self.client = client

    @staticmethod
    def _tenant(tenant: Optional[Union[str, int]]) -> tuple[dict[str, Any], dict[str, str]]:
        if tenant is None:
            return {}, {}
        return {}, {"X-Arsenal-Tenant-Id": str(tenant)}

    def me(self) -> Any:
        return self.client.request("GET", "/api/arsenal/me")

    def roots(self, *, tenant: Optional[Union[str, int]] = None) -> Any:
        params, headers = self._tenant(tenant)
        return self.client.request("GET", "/api/arsenal/roots", params=params, headers=headers)

    def tree(self, root: str, path: str = "/", *, tenant: Optional[Union[str, int]] = None) -> Any:
        params, headers = self._tenant(tenant)
        params.update({"root": root, "path": path})
        return self.client.request("GET", "/api/arsenal/tree", params=params, headers=headers)

    def find_item(self, root: str, name: str, path: str = "/", *, tenant: Optional[Union[str, int]] = None) -> dict[str, Any]:
        result = self.tree(root, path, tenant=tenant) or {}
        items = result.get("items", []) if isinstance(result, dict) else []
        wanted = name.strip().lower()
        for item in items:
            if not isinstance(item, dict):
                continue
            candidates = [item.get("name"), item.get("displayName"), item.get("logicalPath")]
            for candidate in candidates:
                if candidate is None:
                    continue
                text = str(candidate).rstrip("/")
                if text.lower() == wanted or Path(text).name.lower() == wanted:
                    return item
        raise StratumNotFoundError(f"Arsenal item not found: {root}:{path}/{name}", status_code=404)

    def item(self, item_id: int, *, tenant: Optional[Union[str, int]] = None) -> Any:
        params, headers = self._tenant(tenant)
        params["id"] = int(item_id)
        return self.client.request("GET", "/api/arsenal/item", params=params, headers=headers)

    def content(self, item_id: int, *, tenant: Optional[Union[str, int]] = None) -> Any:
        params, headers = self._tenant(tenant)
        params["id"] = int(item_id)
        return self.client.request("GET", "/api/arsenal/content", params=params, headers=headers)

    def history(self, item_id: int, *, tenant: Optional[Union[str, int]] = None) -> Any:
        params, headers = self._tenant(tenant)
        params["id"] = int(item_id)
        return self.client.request("GET", "/api/arsenal/history", params=params, headers=headers)

    def activity(self, *, tenant: Optional[Union[str, int]] = None, **query: Any) -> Any:
        params, headers = self._tenant(tenant)
        params.update(query)
        return self.client.request("GET", "/api/arsenal/activity", params=params, headers=headers)

    def jobs(self, *, tenant: Optional[Union[str, int]] = None, **query: Any) -> Any:
        params, headers = self._tenant(tenant)
        params.update(query)
        return self.client.request("GET", "/api/arsenal/jobs", params=params, headers=headers)

    def job(self, job_id: int, *, tenant: Optional[Union[str, int]] = None) -> Any:
        params, headers = self._tenant(tenant)
        params["id"] = int(job_id)
        return self.client.request("GET", "/api/arsenal/job", params=params, headers=headers)

    def bundle_candidates(self, *, tenant: Optional[Union[str, int]] = None) -> Any:
        params, headers = self._tenant(tenant)
        return self.client.request("GET", "/api/arsenal/bundle-candidates", params=params, headers=headers)

    def promotable_vms(self, *, tenant: Optional[Union[str, int]] = None) -> Any:
        params, headers = self._tenant(tenant)
        return self.client.request("GET", "/api/arsenal/promotable-vms", params=params, headers=headers)

    def create_folder(self, root: str, path: str, name: str, *, comment: str = "", tenant: Optional[Union[str, int]] = None) -> Any:
        params, headers = self._tenant(tenant)
        return self.client.request(
            "POST", "/api/arsenal/folders", params=params, headers=headers,
            json={"root": root, "path": path, "name": name, "comment": comment},
        )

    def rename(self, item_id: int, new_name: str, *, comment: str = "", tenant: Optional[Union[str, int]] = None) -> Any:
        params, headers = self._tenant(tenant)
        return self.client.request(
            "POST", "/api/arsenal/items/rename", params=params, headers=headers,
            json={"itemId": int(item_id), "newName": new_name, "comment": comment},
        )

    def delete(self, item_id: int, *, comment: str = "", tenant: Optional[Union[str, int]] = None) -> Any:
        params, headers = self._tenant(tenant)
        return self.client.request(
            "POST", "/api/arsenal/items/delete", params=params, headers=headers,
            json={"itemId": int(item_id), "comment": comment},
        )

    def save_content(self, item_id: int, content: str, *, comment: str = "", base_revision_id: Optional[int] = None, tenant: Optional[Union[str, int]] = None) -> Any:
        body: dict[str, Any] = {"itemId": int(item_id), "content": content, "comment": comment}
        if base_revision_id is not None:
            body["baseRevisionId"] = int(base_revision_id)
        params, headers = self._tenant(tenant)
        return self.client.request("POST", "/api/arsenal/items/save", params=params, headers=headers, json=body)

    def activate_revision(self, revision_id: int, *, comment: str = "", tenant: Optional[Union[str, int]] = None) -> Any:
        params, headers = self._tenant(tenant)
        return self.client.request(
            "POST", "/api/arsenal/revisions/activate", params=params, headers=headers,
            json={"revisionId": int(revision_id), "comment": comment},
        )

    def validate_template(self, item_id: int, *, tenant: Optional[Union[str, int]] = None) -> Any:
        params, headers = self._tenant(tenant)
        return self.client.request(
            "POST", "/api/arsenal/validate-template", params=params, headers=headers,
            json={"itemId": int(item_id)},
        )

    def upload_stream(
        self,
        source: Union[str, os.PathLike],
        *,
        root: str,
        path: str = "/",
        name: Optional[str] = None,
        comment: str = "",
        tenant: Optional[Union[str, int]] = None,
        progress: Optional[ProgressCallback] = None,
    ) -> Any:
        source_path = Path(source)
        params, headers = self._tenant(tenant)
        params.update({"root": root, "path": path, "name": name or source_path.name})
        if comment:
            params["comment"] = comment
        return self.client.transport.upload_stream(
            "/api/arsenal/upload-stream", source_path,
            params=params, headers=headers, progress=progress,
        )

    def upload(
        self,
        sources: Sequence[Union[str, os.PathLike]],
        *,
        root: str,
        path: str = "/",
        comment: str = "",
        tenant: Optional[Union[str, int]] = None,
        progress: Optional[ProgressCallback] = None,
    ) -> Any:
        # Upload files individually to keep memory use bounded and progress
        # reporting consistent.
        results = []
        for source in sources:
            results.append(self.upload_stream(
                source, root=root, path=path, comment=comment,
                tenant=tenant, progress=progress,
            ))
        return results

    def download(self, item_id: int, destination: Union[str, os.PathLike], *, tenant: Optional[Union[str, int]] = None, progress: Optional[ProgressCallback] = None) -> Path:
        params, headers = self._tenant(tenant)
        params["id"] = int(item_id)
        return self.client.transport.download(
            "GET", "/api/arsenal/download", destination,
            params=params, headers=headers, progress=progress,
        )

    def create_image(self, *, root: str, path: str, name: str, capacity_bytes: int, format: str = "qcow2", comment: str = "", tenant: Optional[Union[str, int]] = None) -> Any:
        params, headers = self._tenant(tenant)
        return self.client.request(
            "POST", "/api/arsenal/images/create", params=params, headers=headers,
            json={"root": root, "path": path, "name": name, "format": format, "capacityBytes": int(capacity_bytes), "comment": comment},
        )

    def grow_image(self, item_id: int, new_capacity_bytes: int, *, comment: str = "", tenant: Optional[Union[str, int]] = None) -> Any:
        params, headers = self._tenant(tenant)
        return self.client.request(
            "POST", "/api/arsenal/images/grow", params=params, headers=headers,
            json={"itemId": int(item_id), "newCapacityBytes": int(new_capacity_bytes), "comment": comment},
        )

    def promote_vm(self, *, item_id: Optional[int] = None, template_item_id: Optional[int] = None, version_tag: str = "", comment: str = "", tenant: Optional[Union[str, int]] = None, **extra: Any) -> Any:
        body: dict[str, Any] = dict(extra)
        if item_id is not None:
            body["itemId"] = int(item_id)
        if template_item_id is not None:
            body["templateItemId"] = int(template_item_id)
        if version_tag:
            body["versionTag"] = version_tag
        if comment:
            body["comment"] = comment
        params, headers = self._tenant(tenant)
        return self.client.request("POST", "/api/arsenal/images/promote", params=params, headers=headers, json=body)

    def create_vm_image_version(self, root: str, template_item_id: int, version_tag: str, *, comment: str = "", tenant: Optional[Union[str, int]] = None) -> Any:
        params, headers = self._tenant(tenant)
        return self.client.request(
            "POST", "/api/arsenal/vm-images/create-version", params=params, headers=headers,
            json={"root": root, "templateItemId": int(template_item_id), "versionTag": version_tag, "comment": comment},
        )


class TemplateManager:
    def __init__(self, client: Any) -> None:
        self.client = client

    def list(self, *, refresh: bool = False) -> list[Template]:
        data = self.client.request("GET", "/api/list/templates/", params={"refresh": str(bool(refresh)).lower()})
        items: list[dict[str, Any]] = []
        if isinstance(data, list):
            items = [dict(x) for x in data if isinstance(x, dict)]
        elif isinstance(data, dict):
            source = data.get("templates") or data.get("items") or data
            if isinstance(source, list):
                items = [dict(x) for x in source if isinstance(x, dict)]
            elif isinstance(source, dict):
                for key, value in source.items():
                    if isinstance(value, dict):
                        item = dict(value)
                        item.setdefault("template", key)
                        items.append(item)
        out = []
        for item in items:
            name = str(item.get("template") or item.get("name") or item.get("slug") or "")
            out.append(Template(self.client, name=name, raw=item))
        return out

    def get(self, template: str) -> Template:
        data = self.client.request("GET", f"/api/list/templates/{quote(template, safe='')}") or {}
        if isinstance(data, dict):
            raw = data.get("template") if isinstance(data.get("template"), dict) else data
            return Template(self.client, name=template, raw=dict(raw))
        return Template(self.client, name=template, raw={"value": data})

    def create(self, name: str, *, path: str = "/", root: str = "templates", tenant: Optional[Union[str, int]] = None, **settings: Any) -> Any:
        body = {"root": root, "path": path, "name": name}
        body.update(settings)
        params, headers = self.client.arsenal._tenant(tenant)
        return self.client.request("POST", "/api/arsenal/templates/create", params=params, headers=headers, json=body)

    def _item_id(self, item: Union[int, str], *, path: str = "/", tenant: Optional[Union[str, int]] = None) -> int:
        if isinstance(item, int) or str(item).isdigit():
            return int(item)
        found = self.client.arsenal.find_item("templates", str(item), path, tenant=tenant)
        value = found.get("id") or found.get("itemId")
        if value is None:
            raise StratumNotFoundError(f"template Arsenal item has no id: {item}", status_code=404)
        return int(value)

    def delete(self, item: Union[int, str], *, path: str = "/", tenant: Optional[Union[str, int]] = None, comment: str = "") -> Any:
        return self.client.arsenal.delete(self._item_id(item, path=path, tenant=tenant), tenant=tenant, comment=comment)

    def rename(self, item: Union[int, str], new_name: str, *, path: str = "/", tenant: Optional[Union[str, int]] = None, comment: str = "") -> Any:
        return self.client.arsenal.rename(self._item_id(item, path=path, tenant=tenant), new_name, tenant=tenant, comment=comment)

    def import_(self, source: Union[str, os.PathLike], **kwargs: Any) -> Any:
        return self.client.bundles.import_(source, **kwargs)


class BundleManager:
    def __init__(self, client: Any) -> None:
        self.client = client

    def import_(
        self,
        source: Union[str, os.PathLike],
        *,
        template_name: Optional[str] = None,
        comment: str = "",
        tenant: Optional[Union[str, int]] = None,
        progress: Optional[ProgressCallback] = None,
    ) -> Any:
        params, headers = self.client.arsenal._tenant(tenant)
        fields: dict[str, Any] = {"comment": comment}
        if template_name:
            fields["templateName"] = template_name
        return self.client.transport.multipart(
            "POST", "/api/arsenal/template-import",
            params=params, headers=headers, fields=fields,
            file_fields={"file": source}, progress=progress,
        )

    import_bundle = import_

    def export(
        self,
        destination: Union[str, os.PathLike],
        *,
        name: str = "",
        description: str = "",
        template_item_id: Optional[int] = None,
        vm_image_item_ids: Optional[Iterable[int]] = None,
        iso_item_ids: Optional[Iterable[int]] = None,
        tenant: Optional[Union[str, int]] = None,
        progress: Optional[ProgressCallback] = None,
    ) -> Path:
        body = {
            "name": name,
            "description": description,
            "templateItemId": int(template_item_id or 0),
            "vmImageItemIds": [int(x) for x in (vm_image_item_ids or [])],
            "isoItemIds": [int(x) for x in (iso_item_ids or [])],
        }
        params, headers = self.client.arsenal._tenant(tenant)
        return self.client.transport.download(
            "POST", "/api/arsenal/bundle-export", destination,
            params=params, headers=headers, json=body, progress=progress,
        )

    export_bundle = export

    def candidates(self, *, tenant: Optional[Union[str, int]] = None) -> Any:
        return self.client.arsenal.bundle_candidates(tenant=tenant)


class MediaManager:
    def __init__(self, client: Any) -> None:
        self.client = client

    @staticmethod
    def _asset(client: Any, raw: Mapping[str, Any]) -> MediaItem:
        return MediaItem(
            client=client,
            id=str(raw.get("id") or ""),
            name=str(raw.get("name") or ""),
            kind=str(raw.get("kind") or ""),
            raw=dict(raw),
        )

    def catalog(self) -> dict[str, list[MediaItem]]:
        data = self.client.request("GET", "/api/stratum/media/catalog") or {}
        out = {"isos": [], "guestTools": []}
        if isinstance(data, dict):
            out["isos"] = [self._asset(self.client, x) for x in data.get("isos", []) if isinstance(x, dict)]
            out["guestTools"] = [self._asset(self.client, x) for x in data.get("guestTools", []) if isinstance(x, dict)]
        return out

    def list_isos(self) -> list[MediaItem]:
        return self.catalog()["isos"]

    def upload_iso(
        self,
        source: Union[str, os.PathLike],
        *,
        path: str = "/",
        name: Optional[str] = None,
        comment: str = "",
        tenant: Optional[Union[str, int]] = None,
        progress: Optional[ProgressCallback] = None,
    ) -> MediaItem:
        source_path = Path(source)
        remote_name = name or source_path.name
        if not remote_name.lower().endswith(".iso"):
            remote_name += ".iso"
        self.client.arsenal.upload_stream(
            source_path, root="iso-library", path=path, name=remote_name,
            comment=comment, tenant=tenant, progress=progress,
        )
        suffixes = (":" + remote_name.lower(), "/" + remote_name.lower())
        for asset in self.list_isos():
            if asset.id.lower().endswith(suffixes) or asset.name.lower() == Path(remote_name).stem.lower():
                return asset
        # Upload succeeded even if a catalog refresh cannot correlate the item.
        return MediaItem(self.client, id="", name=Path(remote_name).stem, kind="arsenal-iso", raw={"uploadedName": remote_name})
