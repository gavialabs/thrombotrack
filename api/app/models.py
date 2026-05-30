import enum
from datetime import datetime
from sqlalchemy import Enum, ForeignKey, func, select
from sqlalchemy.orm import Mapped, mapped_column, column_property, relationship
from sqlalchemy.dialects.postgresql import JSONB
from uuid import UUID, uuid4
# from typing import __future__

from . import db


class EcmoType(enum.Enum):
    GETINGE = "getinge"
    NAUTILUS = "nautilus"


class Ecmo(db.Model):
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(unique=True)
    type: Mapped[EcmoType] = mapped_column(Enum(EcmoType), default=EcmoType.GETINGE)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)


class AnnotationSession(db.Model):
    __tablename__ = "annotation_sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    image_id: Mapped[UUID] = mapped_column(ForeignKey("images.id"))
    started_at: Mapped[datetime] = mapped_column(default=datetime.now)
    ended_at: Mapped[datetime | None]
    mask: Mapped[bytes] = mapped_column(db.LargeBinary)

    clot_area: Mapped[int] = mapped_column(
        default=0
    )  # annotated thrombus area (pixels)
    fibrin_area: Mapped[int] = mapped_column(
        default=0
    )  # annotated fibrin area (pixels)

    image: Mapped["Image"] = relationship(back_populates="annotation_sessions")
    
    segmentations: Mapped[list["Segmentation"]] = relationship(
        back_populates="annotation_session",
        cascade="all, delete-orphan",
        passive_deletes=True
    )


class Image(db.Model):
    __tablename__ = "images"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    ecmo_id: Mapped[UUID] = mapped_column(ForeignKey("ecmo.id"))
    filename: Mapped[str]
    mimetype: Mapped[str]
    original: Mapped[bytes] = mapped_column(db.LargeBinary)
    thumbnail: Mapped[bytes] = mapped_column(db.LargeBinary)
    thumbnail_annotated: Mapped[bytes | None] = mapped_column(db.LargeBinary)
    cropped: Mapped[bytes] = mapped_column(db.LargeBinary)
    width_original: Mapped[int]
    height_original: Mapped[int]
    width_cropped: Mapped[int]
    height_cropped: Mapped[int]
    mm2_per_pixel: Mapped[float] = mapped_column(
        db.Float
    )  # explicitly define to use in subquery
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    current_annotation_session_id: Mapped[int | None] = column_property(
        select(AnnotationSession.id)
        .where(AnnotationSession.image_id == id)
        .order_by(AnnotationSession.started_at.desc())
        .limit(1)
        .correlate_except(AnnotationSession)
        .scalar_subquery()
    )

    clot_area: Mapped[float | None] = column_property(
        select(func.sum(AnnotationSession.clot_area) * mm2_per_pixel)
        .where(AnnotationSession.image_id == id, AnnotationSession.ended_at != None)
        .correlate_except(AnnotationSession)
        .scalar_subquery()
    )

    fibrin_area: Mapped[float | None] = column_property(
        select(func.sum(AnnotationSession.fibrin_area) * mm2_per_pixel)
        .where(AnnotationSession.image_id == id, AnnotationSession.ended_at != None)
        .correlate_except(AnnotationSession)
        .scalar_subquery()
    )

    annotation_sessions: Mapped[list["AnnotationSession"]] = relationship(
        back_populates="image",
        cascade="all, delete-orphan",
        order_by="AnnotationSession.ended_at.desc()",
        passive_deletes=True
    )


class AnnotationType(str, enum.Enum):
    CLOT = "clot"
    FIBRIN = "fibrin"
    ERASE = "erase"


class Segmentation(db.Model):
    __tablename__ = "segmentations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    annotation_session_id: Mapped[UUID] = mapped_column(
        ForeignKey("annotation_sessions.id")
    )
    thrombus_type: Mapped[AnnotationType] = mapped_column(Enum(AnnotationType))
    path: Mapped[list[list[int]]] = mapped_column(JSONB)
    mask: Mapped[bytes] = mapped_column(db.LargeBinary)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    clot_area: Mapped[int]  # explicitly separate these since ERASE segmentations can include both
    fibrin_area: Mapped[int]
    undo: Mapped[bool] = mapped_column(default=False)

    annotation_session: Mapped["AnnotationSession"] = relationship(back_populates="segmentations")
