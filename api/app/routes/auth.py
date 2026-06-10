import os
from flask import (
    Blueprint,
    Response,
    request,
    jsonify,
    redirect,
    session,
)
from flask import (
    Blueprint,
    jsonify,
    request,
)
from typing import Literal

from app import msal_app
from app.schemas import MeSchema
from app.services.auth import upsert_user
from app.decorators import login_required

AUTHORITY = os.environ["AUTHORITY"]
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
API_URL = os.environ["API_URL"]
EXPO_URL = os.environ["EXPO_URL"]

SCOPES = ["openid", "profile", "email"]
REDIRECT_URI = API_URL + "/oidc_callback"

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login")
def login():
    """Initiates Microsoft Entra login.

    Redirects the user to Microsoft Entra login page to enter credentials."""
    auth_url = msal_app.get_authorization_request_url(
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )
    return redirect(auth_url)


@auth_bp.route("/callback")
def auth_callback():
    """Exchanges code, adds user to database, and sets cookie."""
    error = request.args.get("error")
    if error:
        return (
            jsonify(
                {"error": error, "description": request.args.get("error_description")}
            ),
            400,
        )

    code = request.args.get("code")

    # exchange code for a JWT id token containing user information in claims
    result = msal_app.acquire_token_by_authorization_code(
        code,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )

    if "error" in result:
        return jsonify(result), 400

    # extract claims and save or update user object in database
    claims = result["id_token_claims"]

    oid = claims["oid"]
    email = claims.get("email")
    name = claims.get("name")

    user = upsert_user(oid, email, name)

    # store user ID in session cookie
    session.permanent = True  # store for the whole 8-hour expiration
    session["user_id"] = str(user.id)

    return redirect(EXPO_URL)


@auth_bp.route("/me")
@login_required
def me() -> tuple[Response, Literal[200]]:
    """Checks if the user is authenticated.

    Doesn't do anything besides return authentication state and current user ID. The
    @login_required decorator will auto-redirect to /login if the user is not loged in. The web app
    is expected to call this endpoint once on startup-- future calls to endpoints will have their
    own decorator that can redirect, so calling this endpoint with every request is unnecessary.

    Returns:
        MeSchema.
    """
    return (
        jsonify(
            MeSchema().dump({"authenticated": True, "user_id": session["user_id"]})
        ),
        200,
    )
