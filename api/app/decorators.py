"""Function decorators for routes."""

from flask import abort, session, g
from functools import wraps

from . import db
from app.models import User


def login_required(f):
    """Makes the route require a user login to access.
    
    Checks if the Flask session has a user ID stored and fetches the user in the database. If there
    is no user ID or the user does not exist, returns 401 Unauthorized."""
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
