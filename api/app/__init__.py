import msal
import os
from datetime import timedelta
from dotenv import load_dotenv
from flask import Flask, Blueprint
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy.orm import DeclarativeBase

load_dotenv()

AUTHORITY = os.environ["AUTHORITY"]
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
ma = Marshmallow()
msal_app = msal.ConfidentialClientApplication(
    CLIENT_ID,
    authority=AUTHORITY,
    client_credential=CLIENT_SECRET,
)


def create_app():
    app = Flask(__name__)
    CORS(
        app,
        supports_credentials=True,  # allow cookies to be submitted across domains
        origins=[
            "http://localhost:8081",
            # "https://95bf-24-22-134-158.ngrok-free.app"
        ],
    )
    app.config.update(
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL"),
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-secret-key"),
    )

    if os.getenv("FLASK_ENV") == "production":
        app.config.update(
            SESSION_COOKIE_SAMESITE="None",  # allow cross-domain cookies
            SESSION_COOKIE_SECURE=True,  # only send cookies over HTTPS requests
            SESSION_COOKIE_HTTPONLY=True,  # no JS access to cookies
            PERMANENT_SESSION_LIFETIME=timedelta(hours=8),  # cookies expire after 8 hours
        )

    db.init_app(app)
    ma.init_app(app)

    from .routes.oxygenators import ecmo_bp
    from .routes.auth import auth_bp

    bp = Blueprint("main", __name__, url_prefix="/api")

    bp.register_blueprint(ecmo_bp)
    bp.register_blueprint(auth_bp)

    app.register_blueprint(bp)

    return app
