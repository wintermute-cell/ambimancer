from .ambience_manager import get_by_uid
from threading import Lock

thread_lock = Lock()


def init(socketio):

    @socketio.event
    def ambience_set_active(msg):

        # obtain message information
        uid = msg['uid']
        ambience_name = msg['ambience_name']

        # get the corresponding ambience_manager
        ambi_manager = get_by_uid(uid)

        for ambience in ambi_manager.current_ambiences:
            if ambience.name == ambience_name:
                # ambience already active, nothing to do
                return

        # set the ambience active
        ambi_manager.ambience_set_active(ambience_name)

    @socketio.event
    def ambience_set_inactive(msg):

        # obtain message information
        uid = msg['uid']
        ambience_name = msg['ambience_name']

        # get the corresponding ambience_manager
        ambi_manager = get_by_uid(uid)

        for ambience in ambi_manager.current_ambiences:
            if ambience.name == ambience_name:
                ambi_manager.ambience_set_inactive(ambience_name)
                return
