from flask import Flask
from flask_cors import CORS


def create_app(config_object) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object)
    CORS(app)
    return app


