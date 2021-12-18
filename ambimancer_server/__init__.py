from flask import Flask


# application factory
def create_app():
    server = Flask(__name__)

    server.config.from_mapping(
        # place configuration according to
        # https://flask.palletsprojects.com/en/2.0.x/config/
        # in this block.
        debug=True,
    )

    # importing and registering blueprints
    # (every endpoint should be defined as a blueprint)

    # core endpoint, serving the svelte client.
    from ambimancer_server.endpoints import endp_core
    server.register_blueprint(endp_core.bp)

    from ambimancer_server.endpoints import endp_motd
    server.register_blueprint(endp_motd.bp)

    return server
