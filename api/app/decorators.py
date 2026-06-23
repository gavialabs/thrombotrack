from flask import abort, session, g
from functools import wraps

from . import db
from .models import User


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            abort(401)

        user = db.session.get(User, user_id)
        if user is None:
            session.clear()
            abort(401)

        g.user = user
        return f(*args, **kwargs)

    return decorated
