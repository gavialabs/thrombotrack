import jwt
import os
import jwt
import requests
from functools import wraps
from flask import Blueprint, request, jsonify, g
from jwt.algorithms import RSAAlgorithm
import json
from ..utils.session import create_session_token

from flask import (
    Blueprint,
    current_app as app,
    jsonify,
    make_response,
    redirect,
    request,
    session,
)

from ..services.auth import build_saml_auth, extract_uwnetid, issue_jwt 

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

TENANT_ID = os.environ["AZURE_TENANT_ID"]
CLIENT_ID = os.environ["AZURE_CLIENT_ID"]
JWKS_URI  = f"https://login.microsoftonline.com/{TENANT_ID}/discovery/v2.0/keys"

def _get_azure_public_keys():
    """Fetch Azure's public signing keys (cache this in production)."""
    return requests.get(JWKS_URI).json()["keys"]

def _verify_id_token(id_token: str) -> dict:
    """Verify the Azure ID token signature and claims, return the claims."""
    keys = _get_azure_public_keys()

    # Match the key by `kid` in the token header
    header  = jwt.get_unverified_header(id_token)
    pub_key = next(
        RSAAlgorithm.from_jwk(json.dumps(k))
        for k in keys
        if k["kid"] == header["kid"]
    )

    return jwt.decode(
        id_token,
        pub_key,
        algorithms=["RS256"],
        audience=CLIENT_ID,   # must match your app's client ID
        options={"verify_exp": True},
    )

@auth_bp.route("/verify", methods=["POST"])
def verify():
    id_token = request.json.get("id_token")
    if not id_token:
        return jsonify({"error": "Missing id_token"}), 400

    try:
        claims = _verify_id_token(id_token)
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError as e:
        return jsonify({"error": f"Invalid token: {e}"}), 401

    # Upsert user into your database
    user = upsert_user(
        oid=claims["oid"],                          # stable unique ID across apps
        email=claims.get("preferred_username", ""),
        name=claims.get("name", ""),
    )

    # Issue your own session token for subsequent API calls
    session_token = create_session_token(user.id)  # your own JWT or opaque token

    return jsonify({"user": user.to_dict(), "session_token": session_token})
