import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.core.provenance import DataOrigin
from backend.app.core.settings import get_settings


def compute_sha256(file_path: Path) -> str:
    """Computes the SHA-256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    return sha256.hexdigest()


class DatasetManifest(BaseModel):
    dataset_id: str
    district_id: str
    source: str
    dataset_name: str
    version: Optional[str] = None
    license: str
    access_date: str
    bbox: List[float]
    crs: str
    resolution: str
    file_paths: List[str]
    checksums: Dict[str, str]
    processing_status: str = "raw_downloaded"
    script: str
    data_origin: DataOrigin = DataOrigin.CACHED
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def save_manifest(manifest: DatasetManifest, filename: Optional[str] = None) -> Path:
    """Saves dataset manifest JSON to data/metadata/."""
    settings = get_settings()
    metadata_dir = settings.DATA_PATH / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)

    name = filename or f"{manifest.district_id}_{manifest.dataset_id}_manifest.json"
    manifest_path = metadata_dir / name

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest.model_dump(), f, indent=2)

    return manifest_path


def load_manifest(manifest_path: Path) -> DatasetManifest:
    """Loads a dataset manifest JSON from path."""
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return DatasetManifest(**data)
