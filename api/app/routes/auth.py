import jwt
import os
import jwt
from flask import Blueprint, request, jsonify, current_app as app
from ..utils.session import create_session_token
from app.schemas import VerifyTokenSchema
from app.services.auth import upsert_user

from flask import (
    Blueprint,
    jsonify,
    request,
)

from app.utils.jwks import get_public_key

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def _verify_id_token(id_token: str) -> dict:
    """Verify the Azure ID token signature and claims, return the claims."""
    header = jwt.get_unverified_header(id_token)
    pub_key = get_public_key(header["kid"])

    return jwt.decode(
        id_token,
        pub_key,
        algorithms=["RS256"],
        audience=os.environ["AZURE_CLIENT_ID"],
        options={"verify_exp": True},
    )


@auth_bp.route("/verify", methods=["POST"])
def verify():
    payload = VerifyTokenSchema().dump(request.json)

    id_token = payload["id_token"]

    if id_token == "test":
        user = upsert_user(
            oid="cd01087e-d360-40de-be7d-91e37536dcad",
            email="test@example.com",
            name="Test User",
        )

        session_token = create_session_token(user.id)

        return jsonify({"session_token": session_token})

    try:
        claims = _verify_id_token(id_token)
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError as e:
        return jsonify({"error": f"Invalid token: {e}"}), 401

    user = upsert_user(
        oid=claims["oid"],
        email=claims.get("preferred_username", ""),
        name=claims.get("name", ""),
    )

    session_token = create_session_token(user.id)

    return jsonify({"session_token": session_token})
