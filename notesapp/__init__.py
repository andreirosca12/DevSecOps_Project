import logging

from flask import Flask

from . import db
from .config import Config
from .routes import bp


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    app.logger.setLevel(logging.INFO)

    app.teardown_appcontext(db.close_db)
    app.register_blueprint(bp)

    with app.app_context():
        db.init_db()
    app.logger.info("app started, database initialised")

    return app
