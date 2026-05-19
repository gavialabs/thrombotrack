import enum
from datetime import datetime
from sqlalchemy import ForeignKey, Enum, select
from sqlalchemy.orm import Mapped, mapped_column, column_property
from uuid import UUID, uuid4
from . import db

# class User(db.Model):
#     pass


class Ecmo(db.Model):
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(unique=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)


class AnnotationSession(db.Model):
    __tablename__ = "annotation_sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    image_id: Mapped[UUID] = mapped_column(ForeignKey("images.id"))
    started_at: Mapped[datetime] = mapped_column(default=datetime.now)
    ended_at: Mapped[datetime | None]
    mask: Mapped[bytes] = mapped_column(db.LargeBinary)
    # user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))


class Image(db.Model):
    __tablename__ = "images"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    ecmo_id: Mapped[UUID] = mapped_column(ForeignKey("ecmo.id"))
    filename: Mapped[str]
    mimetype: Mapped[str]
    original: Mapped[bytes] = mapped_column(db.LargeBinary)
    cropped: Mapped[bytes] = mapped_column(db.LargeBinary)
    width_original: Mapped[int]
    height_original: Mapped[int]
    width_cropped: Mapped[int]
    height_cropped: Mapped[int]
    mm2_per_pixel: Mapped[float]
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    current_annotation_session_id: Mapped[int | None] = column_property(
        select(AnnotationSession.id)
        .where(AnnotationSession.image_id == id)
        .order_by(AnnotationSession.started_at.desc())
        .limit(1)
        .correlate_except(AnnotationSession)
        .scalar_subquery()
    )


class PromptType(enum.Enum):
    CIRCLE = "circle"
    POINT = "point"


class ThrombusType(enum.Enum):
    CLOT = "clot"
    FIBRIN = "fibrin"


class Segmentation(db.Model):
    __tablename__ = "segmentations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    annotation_session_id: Mapped[UUID] = mapped_column(
        ForeignKey("annotation_sessions.id")
    )
    prompt_type: Mapped[PromptType] = mapped_column(Enum(PromptType))
    thrombus_type: Mapped[ThrombusType] = mapped_column(Enum(ThrombusType))
    x1: Mapped[int]
    y1: Mapped[int]
    x2: Mapped[int | None]
    y2: Mapped[int | None]
    mask: Mapped[bytes] = mapped_column(db.LargeBinary)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    area: Mapped[int]
