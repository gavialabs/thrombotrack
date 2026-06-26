"""Services for interacting with Users in the database."""

from .. import db
from app.models import User


def upsert_user(oid: str, email: str, name: str) -> User:
    """Updates or inserts a User in the database.

    Checks if a user exists with the given object ID (unique across Microsoft Azure). If so,
    updates our database with latest email and name. Otherwise, inserts a new User.

    Args:
        oid: Object ID from Microsoft Azure.
        email: User's email.
        name: User's name.

    Returns:
        New/updated User object.
    """
    stmt = db.select(User).filter_by(object_id=oid)
    user: User | None = db.session.execute(stmt).scalar_one_or_none()

    if user is None:
        user = User(object_id=oid, email=email, name=name)
        db.session.add(user)
    else:
        user.email = email
        user.name = name

    db.session.commit()

    return user
