from definitions import ROOT_DIR, EMITTER_TICK
import os
from os import makedirs
import json
import threading
from time import perf_counter
import random
import copy

ambience_managers = {}


def get_by_uid(uid):
    global ambience_managers
    return ambience_managers[uid]


class Music():
    def __init__(self,
                 volume, shuffle, crossfade_bysecs, pause_bysecs, tracks):
        self.volume = volume  # general music volume
        self.shuffle = shuffle
        self.crossfade_bysecs = crossfade_bysecs
        self.pause_bysecs = pause_bysecs

        # a list of dicts with 'name', 'volume' and 'length'
        self.tracks = tracks
        self.num_tracks = len(tracks)
        self.track_playing_for = 0
        self.current_track = None
        self.current_track_idx = None
        if self.shuffle == 1:
            self.shuffle_list = random.sample(
                range(0, self.num_tracks),
                self.num_tracks
            )

    # calculates the currently playing track, setting a new one if required.
    # then, increments playtime for the current song and returns the new track,
    # together with information on wether or not the track has changed.
    def tick(self):
        # if there is no track playing, set the first one in the list.
        if self.current_track is None:
            self.set_current_track(0)
            is_new = True

        # otherwise determine if a new one should be set.
        else:
            # calculate time left to play the current song for
            time_left = self.current_track['length'] - self.track_playing_for

            is_new = False

            # handle crossfade
            if self.crossfade_bysecs['active']:
                if time_left <= self.crossfade_bysecs['by_secs']:
                    self.set_current_track(self.current_track_index + 1)
                    is_new = True

            # handle pause
            elif self.pause_bysecs['active']:
                if time_left <= 0 - self.pause_bysecs['by_secs']:
                    self.set_current_track(self.current_track_index + 1)
                    is_new = True

            # if neither crossfade nor pause
            else:
                if time_left <= 0:
                    self.set_current_track(self.current_track_index + 1)
                    is_new = True

        # increment playtime
        self.track_playing_for += EMITTER_TICK

        return self.current_track, is_new

    # sets self.current_track to the given track index, respecting the
    # existing shuffle list, and recreating it if required.
    # also sets the current_track_index to the given one after finishing.
    def set_current_track(self, idx):
        # loop around at the end. (and regenerate the shuffle list)
        if idx >= self.num_tracks:
            print('looping music playlist!')
            idx = 0
            if self.shuffle == 1:
                self.shuffle_list = random.sample(
                    range(0, self.num_tracks),
                    self.num_tracks
                )

        # set the new track
        if self.shuffle == 1:
            self.current_track = self.tracks[self.shuffle_list[idx]]
        else:
            self.current_track = self.tracks[idx]

        self.current_track_index = idx
        self.track_playing_for = 0


class SfxTrack():
    def __init__(self, name, chance, volume):
        self.name = name
        self.chance = chance
        self.volume = volume


class SfxLayer():
    def __init__(self,
                 name, volume, interval, tracks):
        self.name = name
        self.volume = volume
        self.interval = interval
        self.tracks = []
        for track in tracks:
            self.tracks.append(SfxTrack(
                track['name'],
                track['chance'],
                track['volume']
            ))

        self.cooldown = 0
        self.current_sfx_index = 0

        # get a cooldown in the interval range to start with.
        self.refresh_cooldown()

    # increments layer time by one EMITTER_TICK and
    # returns SFX if it should be played.
    def tick(self):
        self.cooldown -= EMITTER_TICK
        if self.cooldown <= 0:
            self.refresh_cooldown()
            track = self.get_next_track()
            track = copy.deepcopy(track)  # copy, to not to modify original
            track.volume *= self.volume
            return track
        return None

    def refresh_cooldown(self):
        self.cooldown = random.randrange(self.interval[0], self.interval[1])

    def get_next_track(self):
        idx = random.choices(
            population=list(range(0, len(self.tracks))),
            weights=[track.chance for track in self.tracks],
            k=1
        )[0]
        return self.tracks[idx]


# a list of sfx layers.
class Sfx():
    def __init__(self,
                 volume, layers):
        self.volume = volume
        self.layers = []
        for layer in layers:
            self.layers.append(SfxLayer(
                layer['name'],
                layer['volume'],
                layer['interval'],
                layer['tracks']
            ))

    # increments time in every layer,
    # and returns a list of sounds to be played
    # in that time-tick.
    def tick(self):
        sfx_list = []
        for layer in self.layers:
            if len(layer.tracks) > 0:
                track = layer.tick()
                if track is not None:  # (not every tick returns a track.)
                    track.volume *= self.volume
                    sfx_list.append(track)
        return sfx_list


class Ambience():
    def __init__(self,
                 name, music, sfx):
        self.name = name
        self.music = music
        self.sfx = sfx


class AmbienceManager():
    # room_uuid is used for direction the socket
    # emits to a particular socketio room.
    # uid is used to identify the location of the admin users persistant files.
    def __init__(self, room_uuid, uid:str):
        self.isPlaying = False
        self.current_ambiences = []
        self.room_uuid = room_uuid
        self.uid = uid

    def ambience_load(self, name:str):
        """Loads the file NAME.json into an ambience."""
        fpath = os.path.join(ROOT_DIR, f'file/{self.uid}/ambience/{name}.json')
        with open(fpath) as file:
            ambi_data = json.load(file)
            mus_data = ambi_data['music']
            sfx_data = ambi_data['sfx']

            music = Music(
                mus_data['volume'],
                mus_data['shuffle'],
                mus_data['crossfade'],
                mus_data['pause'],
                mus_data['tracks']
            )
            sfx = Sfx(
                sfx_data['volume'],
                sfx_data['layers']
            )

            ambience = Ambience(
                name,
                music,
                sfx,
            )
            return ambience

    # returns raw json string of ambience file.
    # used by the ambience endpoint to communicate
    # that information to the admin client for editing.
    def ambience_load_json(self, name):
        fpath = os.path.join(ROOT_DIR, f'file/{self.uid}/ambience/{name}.json')
        with open(fpath) as file:
            return file.read()

    def ambience_load_list(self):
        fpath = os.path.join(ROOT_DIR, f'file/{self.uid}/ambience/')
        ls = os.listdir(fpath)
        ambience_names = [f.split('.')[0] for f in ls]
        return ambience_names

    # one instance of this function runs in its own thread for each
    # active ambience_manager
    def ambience_emitter(self, *args):
        socketio = args[0]
        deltatime = 0
        while True:
            # one loop every second
            socketio.sleep(EMITTER_TICK - deltatime)
            if(self.isPlaying):
                begintime = perf_counter()

                # go through each of the currently active ambiences.
                for ambience in self.current_ambiences:
                    # MUSIC

                    # the function below for some reason returns the values
                    current_track, is_new = ambience.music.tick()

                    if is_new:
                        name = current_track['name']
                        volume = current_track['volume'] *\
                            ambience.music.volume
                        socketio.\
                            emit('ambicall_music',
                                 {
                                     'name': f'{name}',
                                     'volume': f'{volume}',
                                     'ambience_name': f'{ambience.name}'
                                 }, room=self.room_uuid)

                    # SFX
                    sfx_this_tick = ambience.sfx.tick()
                    for sfx in sfx_this_tick:
                        print(f'sending sfx to {self.room_uuid}')
                        name = sfx.name
                        volume = sfx.volume
                        socketio.\
                            emit('ambicall_sfx',
                                 {
                                     'name': f'{name}',
                                     'volume': f'{volume}',
                                     'ambience_name': f'{ambience.name}'
                                 }, room=self.room_uuid)

                endtime = perf_counter()
                deltatime = endtime - begintime

    def ambience_set_inactive(self, name):
        for ambience in self.current_ambiences:
            if ambience.name == name:
                self.current_ambiences.remove(ambience)
                # make ambi_call that the clients stop all associated sounds
                break
        if len(self.current_ambiences) == 0:
            self.isPlaying = False

    def ambience_set_active(self, name):
        ambience = self.ambience_load(name)
        self.current_ambiences.append(ambience)
        self.isPlaying = True

    # this function is given a list of strings, describing the path to the
    # target parameter to modify, and a new_val(..ue) to change
    # that parameter to.
    def live_edit(self, ambience_name, target_path, new_val):

        # search the ambience in the list of currently active ones.
        target_ambience = None
        for ambience in self.current_ambiences:
            if ambience.name == ambience_name:
                target_ambience = ambience
        if target_ambience is None:
            # the ambience was not found -> is not active.
            return

        current_step = target_ambience
        max_step_idx = len(target_path)
        for idx, next_step in enumerate(target_path):
            if hasattr(current_step, next_step):
                if idx == max_step_idx-1:
                    current_step.__dict__[next_step] = new_val
                    # TODO: inform clients about the change.
                    break
                current_step = current_step.__dict__[next_step]


def init_new_admin(uid: str) -> None:
    """ creates a new directory structure for the user, if it didn't yet exist.

        this function runs once when a new room is created, also
        creating a new directory structure for the user,
        if it didn't yet exist.

        Parameters
        ---
        uid : str
            The unique identifier belonging to the user.
    """
    ambience_path = os.path.join(ROOT_DIR, f'file/{uid}/ambience/')
    makedirs(ambience_path, exist_ok=True)
    return


# runs a new AmbienceManager for the given uid
def run_new_instance(socketio, room_uuid, uid):
    global ambience_managers

    # an ambience manager already exists, so nothing needs to be done
    # here. the client will just be handed the old manager when trying
    # to connect.
    if uid in ambience_managers:
        print(f'An ambience manager already exists for uid {uid}!')
        return

    print(f'Starting a new ambience manager for uid {uid} and\
          room_uuid {room_uuid}.')

    init_new_admin(uid)
    ambi_manager = AmbienceManager(room_uuid, uid)
    ambience_managers[uid] = ambi_manager

    thread_lock = threading.Lock()
    with thread_lock:
        socketio.\
            start_background_task(
                ambi_manager.ambience_emitter,
                socketio
            )
