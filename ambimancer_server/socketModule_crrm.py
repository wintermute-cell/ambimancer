# create and remove new ambiences for a user.
from definitions import ROOT_DIR
import os

NEW_FILENAME = "New Ambience"


def generate_filename(uid):
    global NEW_FILENAME

    # increment the file index until a name is found
    # that is not yet taken
    fileidx = 1
    filename = ''
    while True:
        filename = NEW_FILENAME + f' {fileidx}'
        fpath = os.path.join(ROOT_DIR,
                             f'file/{uid}/ambience/{filename}.json')
        if(not os.path.exists(fpath)):
            break
        else:
            fileidx += 1


# used to register the socketModule with the main thread.
def init(socketio):

    # creates a new, empty ambience file on the server for
    # the given user.
    @socketio.event
    def ambience_create(msg):

        # obtain the file path.
        uid = msg['uid']

        # generate a unique filename
        filename = generate_filename(uid)

        # TODO: Create a file using the default template
        # that I don't have cause I left it at home :(
