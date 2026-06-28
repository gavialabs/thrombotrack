"""Endpoints for authentication.

/api/auth:
    GET /login: Initiates Microsoft Entra login.
    GET /callback: Exchanges code for an ID token and sets cookie.
    GET /me: Checks if the user is authenticated.
"""

import os
from flask import (
    Blueprint,
    abort,
    request,
    jsonify,
    redirect,
    session,
)
from typing import Literal
from werkzeug.wrappers import Response

from app import msal_app
from app.schemas import MeSchema
from app.services.auth import upsert_user
from app.decorators import login_required

API_URL = os.environ["API_URL"]
FRONTEND_URL = os.environ["FRONTEND_URL"]

SCOPES = ["email"]
REDIRECT_URI = API_URL + "/api/auth/callback"

# rooted at /api
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
def auth_callback() -> Response:
    """Exchanges code for an ID token and sets cookie.

    Adds user to the database if they do not already exist or updates their information. Stores a
    session cookie containing `user_id` corresponding to our database's ID for the User object.

    Returns:
        Redirect response object back to the Expo frontend."""
    error = request.args.get("error")
    if error:
        abort(400, description=f"{error}: {request.args.get("error_description")}")

    code = request.args.get("code")

    if code is None:
        abort(400, description="code not found")

    # exchange code for a JWT id token containing user information in claims
    result = msal_app.acquire_token_by_authorization_code(
        code,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )

    if "error" in result:
        return abort(400, description=result["error"])

    # extract claims and save or update user object in database
    claims = result["id_token_claims"]

    oid = claims["oid"]
    email = claims.get("email")
    name = claims.get("name")

    # insert/update user in the database
    user = upsert_user(oid, email, name)

    # store user ID in session cookie
    session.permanent = True  # allows us to set the expiration time
    session["user_id"] = str(user.id)

    return redirect(FRONTEND_URL)


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
