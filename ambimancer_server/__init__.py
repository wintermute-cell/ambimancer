from flask import Flask
from os import getenv, makedirs


def init_filesys():
    user_file_path = 'file/'
    makedirs(user_file_path, exist_ok=True)


def create_app():
    server = Flask(__name__)

    CONFIG_TYPE = getenv('CONFIG_TYPE', default='config.DevelopmentConfig')
    server.config.from_object(CONFIG_TYPE)

    init_filesys()

    from ambimancer_server.models import db
    db.init_app(server)

    from ambimancer_server.models import migrate
    migrate.init_app(server, db)

    from ambimancer_server.auth import oauth
    oauth.init_app(server)

    from ambimancer_server import socket_handler
    socket_handler.init_app(server)

    # -------------------------------------------------
    # importing and registering blueprints
    # (every endpoint should be defined as a blueprint)

    # core endpoint, serving the svelte client.
    from ambimancer_server.endpoints import endp_core
    server.register_blueprint(endp_core.bp)

    # room creation endpoint.
    from ambimancer_server.endpoints import endp_rooms
    server.register_blueprint(endp_rooms.bp)

    # ambience json data loading and writing endpoint.
    from ambimancer_server.endpoints import endp_ambiences
    server.register_blueprint(endp_ambiences.bp)

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
