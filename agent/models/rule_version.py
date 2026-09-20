"""RuleVersion — tracks installed YARA / detection rule packs."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RuleVersion(BaseModel):
    """Metadata for an installed rule pack version."""

    pack: str = Field(description="Name of the rule pack (e.g. yara-community, custom)")
    version: str = Field(description="Semantic version of the pack")
    hash_signature: str = Field(description="SHA-256 hash of the rule pack contents")
    installed_at: datetime = Field(description="When this version was installed")
