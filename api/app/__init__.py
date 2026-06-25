import msal
import os
from datetime import timedelta
from dotenv import load_dotenv
from flask import Flask, Blueprint
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy.orm import DeclarativeBase
from urllib.parse import quote
from sqlalchemy.engine import URL
from pathlib import Path

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
            f"https://{os.environ['CLOUDFRONT_DOMAIN_NAME']}"
        ],
    )

    # Construct DATABASE_URL and URL encode the password (in case there are odd characters like @./\:
    db_user = os.environ["DB_USER"]
    db_pass = os.environ["DB_PASS"]
    db_host = os.environ["DB_HOST"]
    db_name = os.environ["DB_NAME"]
    db_port = os.environ["DB_PORT"]
    
    if not all([db_user, db_pass, db_host, db_name, db_port]):
        raise RuntimeError(f"Missing DB environment variables in {Path(__file__).name}")

    # db_pass_encoded = quote(db_pass)
    # os.environ["DATABASE_URL"] = f"postgresql://{db_user}:{db_pass_encoded}@{db_host}:{db_port}/{db_name}"
    os.environ["DATABASE_URL"] = URL.create(
        drivername="postgresql", 
        username=db_user,
        password=db_pass,
        host=db_host,
        port=int(db_port) if db_port else None,
        database=db_name,
    ).render_as_string(hide_password=False)

    app.config.update(
        SQLALCHEMY_DATABASE_URI=os.environ["DATABASE_URL"],
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
