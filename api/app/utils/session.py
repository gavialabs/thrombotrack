import jwt, os, datetime
from functools import wraps
from flask import request, jsonify, g
from uuid import UUID

SECRET = os.environ["SECRET_KEY"]


def create_session_token(user_id: UUID) -> str:
    return jwt.encode(
        {
            "sub": str(user_id),
            "exp": datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(hours=8),
        },
        SECRET,
        algorithm="HS256",
    )


def decode_session_token(token: str) -> dict:
    return jwt.decode(token, SECRET, algorithms=["HS256"])


# Decorator for protected routes
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization", "").removeprefix("Bearer ")
        try:
            g.user_id = decode_session_token(token)["sub"]
        except jwt.InvalidTokenError:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)

    return decorated
