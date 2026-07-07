"""Initializes the Flask app, SQLAlchemy, Marshmallow, and MSAL.

Also defines CORS configuration, cookie settings, and registers endpoints."""

import msal
import os
from datetime import timedelta
from dotenv import load_dotenv
from flask import Flask, Blueprint
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.engine import URL

load_dotenv()

UW_OIDC_AUTHORITY = os.environ["UW_OIDC_AUTHORITY"]
UW_OIDC_CLIENT_ID = os.environ["UW_OIDC_CLIENT_ID"]
UW_OIDC_CLIENT_SECRET = os.environ["UW_OIDC_CLIENT_SECRET"]


database_url = URL.create(
  drivername='postgresql',
  username=os.environ["DB_USER"],
  password=os.environ["DB_PASS"],
  host=os.environ["DB_HOST"],
  port=os.environ["DB_PORT"],
  database=os.environ["DB_NAME"],
)

class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
ma = Marshmallow()
msal_app = msal.ConfidentialClientApplication(
    UW_OIDC_CLIENT_ID,
    authority=UW_OIDC_AUTHORITY,
    client_credential=UW_OIDC_CLIENT_SECRET,
)


def create_app():
    app = Flask(__name__)
    CORS(
        app,
        supports_credentials=True,  # allow cookies to be submitted across domains
        origins=[
            f"{os.environ["FRONTEND_URL"]}" if os.environ["FRONTEND_URL"] else "http://localhost:8081",
        ],
    )

    app.config.update(
        SQLALCHEMY_DATABASE_URI=database_url,
        SECRET_KEY=os.getenv("FLASK_SECRET_KEY", "dev-secret-key"),
    )

    if os.getenv("FLASK_ENV") == "production":
        app.config.update(
            # SESSION_COOKIE_SAMESITE="None",  # allow cross-domain cookies
            # SESSION_COOKIE_SECURE=True,  # only send cookies over HTTPS requests
            SESSION_COOKIE_SAMESITE="Lax",  # API and Frontend should have the same domain so okay
            SESSION_COOKIE_HTTPONLY=True,  # no JS access to cookies
            PERMANENT_SESSION_LIFETIME=timedelta(hours=8),  # cookies expire after 8 hours
        )

    db.init_app(app)
    ma.init_app(app)

    from app.routes.oxygenator import oxygenator_bp
    from app.routes.auth import auth_bp
    from app.routes.oxygenator_image import oxygenator_image_bp
    from app.routes.annotation_session import annotation_session_bp
    from app.routes.health import health_bp

    bp = Blueprint("main", __name__, url_prefix="/api")

    bp.register_blueprint(health_bp)
    bp.register_blueprint(auth_bp)
    bp.register_blueprint(oxygenator_bp)
    oxygenator_bp.register_blueprint(oxygenator_image_bp)
    oxygenator_image_bp.register_blueprint(annotation_session_bp)

    app.register_blueprint(bp)

    return app
