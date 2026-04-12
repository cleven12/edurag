from flask import Flask
from flask_cors import CORS
import os

def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY", "change-in-prod")
    CORS(app)

    from .routes import bp
    app.register_blueprint(bp)

    return app