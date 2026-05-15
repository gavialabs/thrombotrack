import datetime
import jwt
import os
from flask import request, current_app as app
from onelogin.saml2.auth import OneLogin_Saml2_Auth

SP_ENTITY_ID = os.environ.get("SP_ENTITY_ID", "https://myapp.cs.washington.edu/saml")
ACS_URL = os.environ.get("ACS_URL", "https://myapp.cs.washington.edu/saml/callback")
SP_BASE_URL = os.environ.get("SP_BASE_URL", "https://myapp.cs.washington.edu")
EXPO_SCHEME = os.environ.get("EXPO_SCHEME", "myexpoapp")  # matches app.json "scheme"
JWT_SECRET = os.environ.get("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 8


def _read_pem(env_var: str, filename: str) -> str:
    """Read a PEM value from an environment variable or a local file."""
    value = os.environ.get(env_var)
    if value:
        # Strip PEM headers if present (python3-saml wants the raw base64)
        return _strip_pem_headers(value)
    if os.path.exists(filename):
        with open(filename) as f:
            return _strip_pem_headers(f.read())
    raise FileNotFoundError(
        f"PEM not found: set {env_var} env var or place {filename} next to app.py"
    )


def _strip_pem_headers(pem: str) -> str:
    lines = [l for l in pem.strip().splitlines() if not l.startswith("-----")]
    return "".join(lines)


def get_saml_settings() -> dict:
    """
    Returns the python3-saml settings dict.
    SP cert/key are read from PEM files on disk (or env vars in production).
    UW IdP values are hard-coded per UW IAM documentation.
    """
    sp_cert = _read_pem("SP_CERT", "sp-cert.pem")
    sp_key = _read_pem("SP_KEY", "sp-key.pem")
    idp_cert = _read_pem(
        "IDP_CERT", "uw-idp-cert.pem"
    )  # extracted from UW metadata XML

    return {
        "strict": True,
        "debug": app.debug,
        "sp": {
            "entityId": SP_ENTITY_ID,
            "assertionConsumerService": {
                "url": ACS_URL,
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
            },
            # UW IdP does NOT support SAML SLO — omit singleLogoutService
            "NameIDFormat": "urn:oasis:names:tc:SAML:2.0:nameid-format:transient",
            "x509cert": sp_cert,
            "privateKey": sp_key,
        },
        "idp": {
            # UW Shibboleth IdP entity ID
            "entityId": "urn:mace:incommon:washington.edu",
            "singleSignOnService": {
                "url": "https://idp.u.washington.edu/idp/profile/SAML2/Redirect/SSO",
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            # No SLO endpoint — UW IdP doesn't support SAML Single Logout
            "x509cert": idp_cert,
        },
        "security": {
            "nameIdEncrypted": False,
            "authnRequestsSigned": False,
            "logoutRequestSigned": False,
            "logoutResponseSigned": False,
            "signMetadata": False,
            "wantMessagesSigned": False,
            "wantAssertionsSigned": True,  # UW signs assertions
            "wantAssertionsEncrypted": False,
            "wantNameId": True,
            "wantNameIdEncrypted": False,
            "wantAttributeStatement": True,
            "requestedAuthnContext": False,
        },
    }


def build_saml_auth() -> OneLogin_Saml2_Auth:
    req = {
        "https": "on" if request.scheme == "https" else "off",
        "http_host": request.host,
        "server_port": request.environ.get("SERVER_PORT", "5002"),
        "script_name": request.path,
        "get_data": request.args.copy(),
        "post_data": request.form.copy(),
        "query_string": request.query_string.decode("utf-8"),
    }
    return OneLogin_Saml2_Auth(req, get_saml_settings())


def issue_jwt(uwnetid: str, attributes: dict) -> str:
    payload = {
        "sub": uwnetid,
        "uwnetid": uwnetid,
        "eppn": attributes.get("eppn", [None])[0],
        "affiliations": attributes.get("affiliations", []),
        "iat": datetime.datetime.now(datetime.timezone.utc),
        "exp": datetime.datetime.now(datetime.timezone.utc)
        + datetime.timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def extract_uwnetid(auth: OneLogin_Saml2_Auth) -> str:
    """
    UW releases uwnetid as an attribute. Fall back to the ePPN prefix
    (javerage@washington.edu → javerage) if needed.
    """
    attrs = auth.get_attributes()
    uwnetid_values = (
        attrs.get("uwnetid") or attrs.get("urn:oid:0.9.2342.19200300.100.1.1") or []
    )
    if uwnetid_values:
        return uwnetid_values[0]
    eppn = (
        attrs.get("eppn") or attrs.get("urn:oid:1.3.6.1.4.1.5923.1.1.1.6") or [None]
    )[0]
    if eppn and "@" in eppn:
        return eppn.split("@")[0]
    raise ValueError("Could not extract uwnetid from SAML attributes")
