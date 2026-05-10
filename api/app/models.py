import enum
from datetime import datetime
from sqlalchemy import ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID, uuid4
from . import db


# class User(db.Model):
#     pass

class Ecmo(db.Model):
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(unique=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)


class Image(db.Model):
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    ecmo_id: Mapped[UUID] = mapped_column(ForeignKey("ecmo.id"))
    filename: Mapped[str]
    original: Mapped[bytes] = mapped_column(db.LargeBinary)
    cropped: Mapped[bytes] = mapped_column(db.LargeBinary)
    width_original: Mapped[int]
    height_original: Mapped[int]
    width_cropped: Mapped[int]
    height_cropped: Mapped[int]
    mm2_per_p2: Mapped[float]
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)


class AnnotationSession(db.Model):
    __tablename__ = "annotation_sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    image_id: Mapped[UUID] = mapped_column(ForeignKey("image.id"))
    started_at: Mapped[datetime]
    ended_at: Mapped[datetime]
    # user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))


class SegmentationType(enum.Enum):
    CIRCLE = "circle"
    POINT = "point"

class Segmentation(db.Model):
    __tablename__ = "segmentations"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    annotation_session_id: Mapped[UUID] = mapped_column(ForeignKey("annotation_session.id"))
    type: Mapped[SegmentationType] = mapped_column(Enum(SegmentationType))
    x1: Mapped[float]
    y1: Mapped[float]
    x2: Mapped[float | None]
    y2: Mapped[float | None]
    mask: Mapped[bytes] = mapped_column(db.LargeBinary)
    created_at: Mapped[datetime]
    # area_px: Mapped[float]
