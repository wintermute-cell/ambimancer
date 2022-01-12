import uuid
from flask_socketio import join_room, leave_room, \
    close_room, rooms, disconnect
from .ambience_manager import run_new_instance
from .socket_handler import socketio

room_uuid_to_uid = {}


# creates a new socketio room for the user with uid
#   (just the license key for now)
# and returns the rooms corresponding uuid.
# the client then has to use that uuid to join the room.
def create_room(uid):
    # the uuid is used for both flask_socketio and client joining
    this_uuid = uuid.uuid4()
    this_uuid = str(this_uuid)

    # the ambience_manager runs for each room uuid separately.
    run_new_instance(socketio, this_uuid, uid)

    # connect the uuid to the uid for later use.
    room_uuid_to_uid[this_uuid] = uid
    return this_uuid


@socketio.on('join_room_request')
def join_room_handler(msg):
    room_uuid = msg['room']
    join_room(room_uuid)
