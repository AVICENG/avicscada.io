from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from uuid import UUID

from avic_core.domain.models import BaseObject


@dataclass(slots=True)
class RepositoryAsset(BaseObject):
    """Station-scoped raster asset stored in the Core repository."""
    station_id: str = ""
    media_type: str = "image/png"
    content_base64: str = ""
    byte_size: int = 0
    content_sha256: str = ""

    def __post_init__(self):
        super(RepositoryAsset, self).__post_init__()
        UUID(self.station_id)
        if self.media_type not in {"image/png", "image/jpeg", "image/gif", "image/webp"}:
            raise ValueError("Поддерживаются только PNG, JPEG, GIF и WebP")
        if not 0 < self.byte_size <= 3 * 1024 * 1024:
            raise ValueError("Размер изображения должен быть от 1 байта до 3 МБ")
