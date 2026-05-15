import jwt
import os
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

auth_bp = Blueprint("saml", __name__, url_prefix="/saml")

JWT_SECRET = os.environ.get("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = "HS256"


@auth_bp.route("/login")
def login():
    """
    SP-initiated login. The Expo app opens this URL in a browser session.
    Redirects the user to the UW Weblogin page.
    """
    auth = build_saml_auth()
    return redirect(auth.login())


@auth_bp.route("/callback", methods=["POST"])
def callback():
    """
    Assertion Consumer Service (ACS) endpoint.
    The UW IdP POSTs the SAML response here after the user authenticates.
    On success, issues a JWT and deep-links back to the Expo app.
    """
    auth = build_saml_auth()
    auth.process_response()

    errors = auth.get_errors()
    if errors:
        app.logger.error("SAML errors: %s — %s", errors, auth.get_last_error_reason())
        return make_response("Authentication failed", 401)

    if not auth.is_authenticated():
        return make_response("Not authenticated", 401)

    try:
        uwnetid = extract_uwnetid(auth)
    except ValueError as e:
        app.logger.error("Attribute extraction failed: %s", e)
        return make_response("Missing required attributes", 401)

    attributes = auth.get_attributes()
    token = issue_jwt(uwnetid, attributes)

    # Store in server-side session as well (optional — useful for web flows)
    session["uwnetid"] = uwnetid
    session["saml_session_index"] = auth.get_session_index()

    # Deep-link back to the Expo app with the JWT
    expo_redirect = f"{EXPO_SCHEME}://auth?token={token}"
    return redirect(expo_redirect)


@auth_bp.route("/saml/metadata")
def saml_metadata():
    """
    Exposes SP metadata XML. The UW SP Registry fetches this URL during
    registration to auto-populate your SP configuration.
    Register at: https://iam.uw.edu/spreg
    """
    auth = build_saml_auth()
    settings = auth.get_settings()
    metadata = settings.get_sp_metadata()
    errors = settings.validate_metadata(metadata)
    if errors:
        return make_response(", ".join(errors), 500)
    resp = make_response(metadata, 200)
    resp.headers["Content-Type"] = "application/xml"
    return resp


@auth_bp.route("/saml/logout")
def saml_logout():
    """
    Local logout + redirect to UW's logout page.
    Note: The UW IdP does NOT support SAML 2.0 Single Logout (SLO).
    This clears the local session only, then sends users to UW's logout page.
    """
    session.clear()
    return redirect("https://idp.u.washington.edu/idp/logout")


@auth_bp.route("/api/me")
def me():
    """
    Example protected API route. Validates the JWT from the Authorization header.
    Expo app calls this with: Authorization: Bearer <token>
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Missing token"}), 401
    token = auth_header.removeprefix("Bearer ")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return jsonify(
            {
                "uwnetid": payload["uwnetid"],
                "affiliations": payload.get("affiliations", []),
            }
        )
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401
