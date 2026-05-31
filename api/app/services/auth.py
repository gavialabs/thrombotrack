from app.models import User
from app import db

def upsert_user(oid: str, email: str, name: str) -> User:
    user: User | None = db.session.execute(
        db.select(User).filter_by(object_id=oid)
    ).scalar_one_or_none()

    if user is None:
        user = User(
            object_id=oid,
            email=email,
            name=name
        )
        db.session.add(user)
    else:
        user.email = email
        user.name = name
    
    db.session.commit()

    return user
