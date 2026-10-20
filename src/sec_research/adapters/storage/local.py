"""Atomic, create-only Bronze publication on a local filesystem."""

import hashlib
import os
import re
import tempfile
from pathlib import Path

from sec_research.contracts.sec import IngestionCode, IngestionError


class LocalBronze:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.objects = self.root / "bronze" / "sha256"

    def path(self, checksum: str) -> Path:
        if not re.fullmatch(r"[0-9a-f]{64}", checksum):
            raise IngestionError(IngestionCode.INTEGRITY)
        target = self.objects / checksum[:2] / checksum
        if not target.resolve().is_relative_to(self.root):
            raise IngestionError(IngestionCode.INTEGRITY)
        return target

    def read(self, checksum: str) -> bytes:
        try:
            body = self.path(checksum).read_bytes()
        except OSError:
            raise IngestionError(IngestionCode.STORAGE, retryable=True) from None
        if hashlib.sha256(body).hexdigest() != checksum:
            raise IngestionError(IngestionCode.INTEGRITY)
        return body

    def put(self, body: bytes) -> tuple[str, str]:
        checksum = hashlib.sha256(body).hexdigest()
        path = self.path(checksum)
        self._publish(path, body)
        self.read(checksum)
        return checksum, path.as_uri()

    def put_manifest(self, manifest_id: str, body: bytes) -> str:
        if not re.fullmatch(r"[0-9a-f]{32}", manifest_id):
            raise IngestionError(IngestionCode.INVALID_METADATA)
        path = self.root / "bronze" / "manifests" / f"{manifest_id}.json"
        self._publish(path, body)
        return path.as_uri()

    def read_manifest(self, manifest_id: str) -> bytes:
        if not re.fullmatch(r"[0-9a-f]{32}", manifest_id):
            raise IngestionError(IngestionCode.INVALID_METADATA)
        try:
            return (self.root / "bronze" / "manifests" / f"{manifest_id}.json").read_bytes()
        except OSError:
            raise IngestionError(IngestionCode.STORAGE, retryable=True) from None

    def _publish(self, path: Path, body: bytes) -> None:
        temporary: str | None = None
        try:
            if not path.resolve().is_relative_to(self.root):
                raise IngestionError(IngestionCode.INTEGRITY)
            path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                dir=path.parent, prefix=".stage-", delete=False
            ) as file:
                temporary = file.name
                file.write(body)
                file.flush()
                os.fsync(file.fileno())
            try:
                # Hard-link publication is atomic and cannot replace an existing object.
                os.link(temporary, path)
            except FileExistsError:
                if path.read_bytes() != body:
                    raise IngestionError(IngestionCode.INTEGRITY) from None
            if os.name != "nt":
                descriptor = os.open(path.parent, os.O_RDONLY)
                try:
                    os.fsync(descriptor)
                finally:
                    os.close(descriptor)
        except OSError:
            raise IngestionError(IngestionCode.STORAGE, retryable=True) from None
        finally:
            if temporary is not None:
                try:
                    Path(temporary).unlink(missing_ok=True)
                except OSError:
                    raise IngestionError(IngestionCode.STORAGE, retryable=True) from None

    def checksums(self) -> list[str]:
        return sorted(
            path.name for path in self.objects.glob("*/*") if not path.name.startswith(".")
        )
