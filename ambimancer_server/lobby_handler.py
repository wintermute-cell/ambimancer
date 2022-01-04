import uuid
from flask_socketio import join_room, leave_room, close_room, rooms, disconnect
from . import ambience_manager

room_ids = []


def Lobby():
    def __init__(self, uuid, ambience_manager):
        self.uuid = uuid
        self.ambience_manager = ambience_manager


def create_lobby(socketio):
    # the uuid is used for both flask_socketio and client
    # client joining
    this_uuid = uuid.uuid4()
    ambience_manager.run(socketio, this_uuid, ambience_manager)
    this_lobby = Lobby(this_uuid, ambience_manager)
