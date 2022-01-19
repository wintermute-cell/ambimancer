from .ambience_manager import get_by_uid
from definitions import ROOT_DIR
import os
from threading import Lock
import json

thread_lock = Lock()


def init(socketio):

    # receives edits from the admin client
    # and applies them (liveedit if required).
    @socketio.event
    def ambience_edit(msg):

        # obtain the file path.
        uid = msg['uid']
        ambience_name = msg['ambience_name']
        fpath = os.path.join(ROOT_DIR,
                             f'file/{uid}/ambience/{ambience_name}.json')

        # load the path to the target line into a list of steps.
        target_path = msg['target'].split('.')

        # run the live edit.
        ambi_manager = get_by_uid(uid)
        # then, check if a liveedit is necessary.
        for ambience in ambi_manager.current_ambiences:
            if ambience.name == msg['ambience_name']:
                # TODO make the liveedit
                break

        # write change to disk only if requested.
        if msg['to_disk']:
            # load the file into a list of lines.
            ambi_obj = None
            with open(fpath) as file:
                ambi_obj = json.load(file)

            # recursive function to find and replace the correct value
            # according to the target_path
            def update_value(obj, step_idx=0):
                for key, val in obj.copy().items():
                    if target_path[step_idx] == key:
                        if key == 'tracks' or key == 'layers':
                            for idx, itm in enumerate(val.copy()):
                                if itm['name'] == target_path[step_idx+1]:
                                    obj[key].append(
                                        update_value(itm, step_idx+2))
                                    del obj[key][idx]

                        if isinstance(val, dict):
                            obj[key] = update_value(val, step_idx+1)
                        elif isinstance(val, list):
                            obj[key] = [
                                update_value(i, step_idx+1) for i in val
                            ]
                        else:
                            obj[key] = str(msg['new_val'])
                return obj

            ambi_obj = update_value(ambi_obj)

            # thread lock the file access to make sure only one thread at
            # a time is writing to the file.
            global thread_lock
            with thread_lock:
                # write the list of lines back to the file.
                with open(fpath, 'w') as file:
                    json.dump(ambi_obj, file)
