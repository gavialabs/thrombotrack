from flask import Blueprint

health_bp = Blueprint("health", __name__, url_prefix="/health")

@health_bp.route("/health")
def health_check():
    return {"status": "healthy"}, 200