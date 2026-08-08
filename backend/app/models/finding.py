import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.scan import Scan


class ScanDependency(Base):
    __tablename__ = "scan_dependencies"
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scans.id"), index=True)
    package_name: Mapped[str | None] = mapped_column(String(255))
    version: Mapped[str | None] = mapped_column(String(255))
    original_requirement: Mapped[str] = mapped_column(Text)
    is_supported: Mapped[bool]
    checked: Mapped[bool]
    unsupported_reason: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    scan: Mapped["Scan"] = relationship(back_populates="dependencies")
    findings: Mapped[list["Finding"]] = relationship(back_populates="scan_dependency")


class Vulnerability(Base):
    __tablename__ = "vulnerabilities"
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    osv_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    summary: Mapped[str | None] = mapped_column(Text)
    details: Mapped[str | None] = mapped_column(Text)
    severity: Mapped[str | None] = mapped_column(String(20))
    advisory_url: Mapped[str | None] = mapped_column(Text)
    raw_osv_data: Mapped[dict[str, Any]] = mapped_column(JSON().with_variant(JSONB(), "postgresql"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Finding(Base):
    __tablename__ = "findings"
    __table_args__ = (
        UniqueConstraint(
            "scan_dependency_id", "vulnerability_id", name="uq_finding_dependency_vulnerability"
        ),
    )
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scans.id"), index=True)
    scan_dependency_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("scan_dependencies.id"), index=True
    )
    vulnerability_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("vulnerabilities.id"), index=True
    )
    fixed_version: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    scan_dependency: Mapped[ScanDependency] = relationship(back_populates="findings")
    vulnerability: Mapped[Vulnerability] = relationship()
