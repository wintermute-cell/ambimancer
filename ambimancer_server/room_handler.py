import uuid
from flask_socketio import SocketIO, join_room, leave_room, \
    close_room, rooms, disconnect
from . import ambience_manager

socketio = None


def init_app(server):
    global socketio
    socketio = SocketIO(server, async_mode=None)


# creates a new socketio room for the user with uid (just the license key for now)
# and returns the rooms corresponding uuid.
# the client then has to use that uuid to join the room.
def create_room(uid):
    global socketio
    # the uuid is used for both flask_socketio and client joining
    this_uuid = uuid.uuid4()
    # the ambience_manager runs for each room uuid separately.
    ambience_manager.run_new_instance(socketio, this_uuid, uid)
    return this_uuid
