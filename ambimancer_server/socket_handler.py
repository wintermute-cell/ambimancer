from flask_socketio import SocketIO

socketio = None


def init_app(server):
    global socketio
    socketio = SocketIO(server, async_mode=None)

    from ambimancer_server import socketModule_edit
    socketModule_edit.init(socketio)

    from ambimancer_server import socketModule_activation
    socketModule_activation.init(socketio)
