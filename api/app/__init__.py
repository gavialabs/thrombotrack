from flask import Flask, Blueprint
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from dotenv import load_dotenv
import os
from sqlalchemy.orm import DeclarativeBase

load_dotenv()

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
ma = Marshmallow()


def create_app():
    app = Flask(__name__)
    CORS(
        app,
        origins=[
            "http://localhost:8081",
            # "https://95bf-24-22-134-158.ngrok-free.app"
        ],
    )
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "uploads")
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    # app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    # app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")

    db.init_app(app)
    
    from .routes.ecmo import ecmo_bp
    from .routes.auth import auth_bp

    bp = Blueprint("main", __name__, url_prefix="/api")
    
    bp.register_blueprint(ecmo_bp)
    bp.register_blueprint(auth_bp)

    app.register_blueprint(bp)

    return app