from .ambience_manager import get_by_uid
from definitions import ROOT_DIR
import os
from threading import Lock

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
            lines = None
            with open(fpath) as file:
                lines = file.readlines()

            # find the target line and replace it in the list.
            target_idx = 0
            line_num = 1
            for line in lines:
                processed = line.strip().split('\"')
                # make sure the line actually contains a key.
                if(len(processed) > 1):
                    key = processed[1]
                    if key == target_path[target_idx]:
                        # check if final step is reached.
                        # If so, line_num is correct.
                        if target_idx == len(target_path)-1:
                            # make sure to append a ',' if required.
                            trailing_comma = ''
                            if line.strip().endswith(','):
                                trailing_comma = ','
                            # reconstruct the line with the new value,
                            # and then end.
                            lines[line_num-1] =\
                                line.split(':')[0] +\
                                ':' + str(msg['new_val']) +\
                                trailing_comma + '\n'
                            break
                        else:
                            target_idx += 1
                line_num += 1

            # thread lock the file access to make sure only one thread at
            # a time is writing to the file.
            global thread_lock
            with thread_lock:
                # write the list of lines back to the file.
                with open(fpath, 'w') as file:
                    for line in lines:
                        file.write(line)
