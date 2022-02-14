from .ambience_manager import get_by_uid
from definitions import ROOT_DIR
import os
from threading import Lock
import json
from tinytag import TinyTag

thread_lock = Lock()


# This function shifts the chances of all tracks in a layer when one of them
# changes, or is inserted as a new one (ergo, changes from 0->x).
# It then returns the chance of the changed track back, and does NOT change
# the chance value of the actually modified track.
def recalc_chances(ambience_object,
                   layer_idx,
                   track_idx=None,
                   new_chance=None):
    existing_tracks =\
        [track for track in
         ambience_object['sfx']['layers'][layer_idx]['tracks']]

    # percentage that the other tracks, beside the changed one,
    # took, summed together, before and after the change.
    old_perc = 0
    if track_idx is None:
        old_perc = 1
        new_chance = 1/(len(existing_tracks)+1)
    else:
        old_perc = 1 - existing_tracks[track_idx]['chance']
    new_perc = 1 - new_chance

    # percentages of the other tracks.
    for idx in range(len(existing_tracks)):
        if old_perc != 0:
            old_percentage = existing_tracks[idx]['chance']/old_perc
        else:
            old_percentage = 1

        ambience_object['sfx']['layers'][layer_idx]['tracks'][idx]['chance'] =\
            new_perc * old_percentage

    return new_chance


def update_value(ambience_object, target_path, new_value):
    # recursive function to find and replace the correct value
    # according to the target_path
    def inner_update_value(obj, step_idx=0):
        for key, val in obj.copy().items():
            if target_path[step_idx] == key:
                # if key == 'tracks' or key == 'layers':
                #    for idx, itm in enumerate(val.copy()):
                #        if itm['name'] == target_path[step_idx+1]:
                #            obj[key].insert(
                #                idx,
                #                inner_update_value(itm, step_idx+2))
                #            del obj[key][idx+1]
                if key == 'interval':
                    obj[key] = new_value
                    return obj

                if isinstance(val, dict):
                    obj[key] = inner_update_value(val, step_idx+1)
                elif isinstance(val, list):
                    list_idx = int(target_path[step_idx+1])
                    original_entry = val[list_idx]
                    del val[list_idx]
                    obj[key].insert(
                        list_idx,
                        inner_update_value(original_entry, step_idx+2)
                    )
                else:
                    obj[key] = new_value
        return obj
    return inner_update_value(ambience_object)


def handle_special_case_rm(ambience_object, target_path):
    type = target_path[1]  # sfx or music
    if type == 'music':
        track_idx = int(target_path[2])
        del ambience_object['music']['tracks'][track_idx]
    elif type == 'sfx':
        layer_idx = int(target_path[2])
        track_idx = int(target_path[3])
        del ambience_object['sfx']['layers'][layer_idx]['tracks'][track_idx]


def write_edit_to_file(file_path, uid, target_path, msg):
    # thread lock the file access to make sure only one thread at
    # a time is writing to the file, and no thread reads
    # while another one is writing.
    global thread_lock
    with thread_lock:
        # load the file into an object.
        ambi_obj = None
        with open(file_path) as file:
            ambi_obj = json.load(file)

        # FIRST, HANDLE SPECIAL CASES #

        # special case: reordering of music tracks
        if target_path[0] == 'reorder_music_track':
            ambi_obj['music']['tracks'][msg['new_val'][0]],\
                ambi_obj['music']['tracks'][msg['new_val'][1]] =\
                ambi_obj['music']['tracks'][msg['new_val'][1]],\
                ambi_obj['music']['tracks'][msg['new_val'][0]],

        # special case: adding of new tracks
        # use add_track like:
        # target_path = add_track.<music|sfx>.<[layer_idx]>
        elif target_path[0] == 'add_track':
            track_json = msg['new_val']
            if target_path[1] == 'music':
                # retrieve track length
                tname = track_json['name']
                trckpath = os.path.join(
                    ROOT_DIR,
                    f'file/{uid}/audio/{target_path[1]}/{tname}.ogg')
                track_json['length'] = TinyTag.get(trckpath).duration

                ambi_obj['music']['tracks'].\
                    append(track_json)
            elif target_path[1] == 'sfx':
                # TODO: Calculate chance for this track and
                # update all tracks accordingly
                layer_idx = int(target_path[2])
                new_chance = recalc_chances(ambi_obj, layer_idx)
                track_json['chance'] = new_chance

                ambi_obj['sfx']['layers'][layer_idx]['tracks'].\
                    append(track_json)

        elif target_path[0] == 'rm':
            handle_special_case_rm(ambi_obj, target_path)

        # THEN, HANDLE THE NORMAL UPDATE #
        else:
            # additional case: modifying sfx chance
            if target_path[-1] == 'chance':
                recalc_chances(
                    ambi_obj,
                    int(target_path[2]),
                    int(target_path[4]),
                    msg['new_val'])

            # finally, if no special case occurrs, do the normal
            # recursive update function
            ambi_obj =\
                update_value(ambi_obj, target_path, msg['new_val'])

        # write the list of lines back to the file.
        with open(file_path, 'w') as file:
            json.dump(ambi_obj, file)


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
            write_edit_to_file(fpath, uid, target_path, msg)
