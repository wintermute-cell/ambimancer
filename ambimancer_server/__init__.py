from flask import Flask
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
import ambience_manager
from os import getenv
from flask_httpauth import HTTPBasicAuth
from flask_migrate import Migrate

db = SQLAlchemy()
auth = HTTPBasicAuth()
migrate = Migrate()


def create_app():
    server = Flask(__name__)

    CONFIG_TYPE = getenv('CONFIG_TYPE', default='config.DevelopmentConfig')
    server.config.from_object(CONFIG_TYPE)

    db.init_app(server)
    migrate.init_app(server, db)

    import ambimancer_server.models

    # socket io for broadcasting instructions to the clients
    socketio = SocketIO(server, async_mode=None)
    ambience_manager.run(socketio)

    # -------------------------------------------------
    # importing and registering blueprints
    # (every endpoint should be defined as a blueprint)

    # core endpoint, serving the svelte client.
    from ambimancer_server.endpoints import endp_core
    server.register_blueprint(endp_core.bp)

    # TODO: to be removed
    from ambimancer_server.endpoints import endp_motd
    server.register_blueprint(endp_motd.bp)

    # admin control endpoint
    from ambimancer_server.endpoints import endp_control
    server.register_blueprint(endp_control.bp)

    # user authentication endpoint
    from ambimancer_server.endpoints import endp_auth
    server.register_blueprint(endp_auth.bp)

    # streaming endpoint
    from ambimancer_server.endpoints import endp_audio
    server.register_blueprint(endp_audio.bp)

    return server
