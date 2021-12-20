from definitions import ROOT_DIR
import os.path
import json
import threading
from time import perf_counter
import random

ambi_manager = None
emitter_thread = None


class Music():
    def __init__(self,
                 volume, shuffle, crossfade_bysecs, pause_bysecs, tracks):
        self.volume = volume
        self.shuffle = shuffle
        self.crossfade_bysecs = crossfade_bysecs
        self.pause_bysecs = pause_bysecs
        self.tracks = list(tracks.values())
        self.num_tracks = len(tracks)

        self.track_playing_for = 0
        self.current_track = None
        self.current_track_idx = None
        if self.shuffle == 1:
            self.shuffle_list = random.sample(
                range(0, self.num_tracks),
                self.num_tracks
            )

    def set_current_track(self, idx):
        # loop around at the end. (and regenerate the shuffle list)
        if idx >= self.num_tracks:
            idx = 0
            if self.shuffle == 1:
                self.shuffle_list = random.sample(
                    range(0, self.num_tracks),
                    self.num_tracks
                )

        if self.shuffle == 1:
            self.current_track = self.tracks[self.shuffle_list[idx]]
        else:
            self.current_track = self.tracks[idx]

        self.current_track_index = idx
        self.track_playing_for = 0

    # returns the currently playing track, and a boolean indicating whether
    # the track is a new track or still the old one
    def get_curr_track(self):
        # if there is no track playing, set the first one in the list.
        if self.current_track is None:
            self.set_current_track(0)
            return self.current_track, True
        # otherwise determine if a new one should be set.
        else:
            time_left = self.current_track['length'] - self.track_playing_for
            if self.crossfade_bysecs['active']:
                if time_left <= self.crossfade_bysecs['by_secs']:
                    self.set_current_track(self.current_track_index + 1)
                    return self.current_track, True
                else:
                    return self.current_track, False

            elif self.pause_bysecs['active']:
                if time_left <= 0 - self.pause_bysecs['by_secs']:
                    self.set_current_track(self.current_track_index + 1)
                    return self.current_track, True
                else:
                    return self.current_track, False

            else:
                if time_left <= 0:
                    self.set_current_track(self.current_track_index + 1)
                    return self.current_track, True
                else:
                    return self.current_track, False


class SfxLayer():
    def __init__(self,
                 volume, shuffle, offset, chance, interval, tracks):
        self.volume = volume
        self.shuffle = shuffle
        self.offset = offset
        self.chance = chance
        self.interval = interval
        self.tracks = list(tracks.values())
        self.num_tracks = len(tracks)

        self.cooldown = 0
        self.current_sfx_index = 0
        self.refresh_cooldown()

    def refresh_cooldown(self):
        timefactor = 1
        timeunit = self.interval['unit']
        if timeunit == 's':
            timefactor = 1
        elif timeunit == 'm':
            timefactor = 60
        elif timeunit == 'h':
            timefactor = 60 ** 2
        else:
            timefactor = 1

        cooldown_offset = random.uniform(0, self.offset)
        self.cooldown = \
            ((timefactor * int(self.interval['time'])) /
             self.interval['amount']) +\
            (cooldown_offset * random.sample([-1, 1], 1)[0])

    def get_next_sfx(self):
        if self.shuffle == 1:
            self.current_sfx_index = random.randint(0, self.num_tracks-1)
            return self.tracks[self.current_sfx_index]
        else:
            self.current_sfx_index += 1
            if self.current_sfx_index >= self.num_tracks:
                self.current_sfx_index = 0
            return self.tracks[self.current_sfx_index]

        return None

    # increments layer time by one second and
    # returns SFX if it should be played.
    def tick_layer(self):
        self.cooldown -= 1
        if self.cooldown <= 0:
            self.refresh_cooldown()

            # see if playing suceeds
            if self.chance > random.random():
                return self.get_next_sfx()


class Sfx():
    def __init__(self,
                 volume, layers):
        self.volume = volume
        self.layers = []
        for layer in list(layers.values()):
            self.layers.append(SfxLayer(
                layer['volume'],
                layer['shuffle'],
                layer['offset'],
                layer['chance'],
                layer['interval'],
                layer['tracks']
            ))

    # increments time in every layer,
    # and returns a list of sounds to be played
    # in that time-tick.
    def tick(self):
        sfx_this_tick = []
        for layer in self.layers:
            track = layer.tick_layer()
            if track is not None:
                track['real_volume'] =\
                    track['volume'] * layer.volume * self.volume
                sfx_this_tick.append(track)
        return sfx_this_tick


class Ambience():
    def __init__(self,
                 name, music, sfx):
        self.name = name
        self.music = music
        self.sfx = sfx


class AmbienceManager():
    def __init__(self):
        self.isPlaying = False
        self.current_ambiences = []

    # loads the file NAME.json into an ambience.
    def ambience_load(self, name):
        fpath = os.path.join(ROOT_DIR, f'file/ambience/{name}.json')
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

    def ambience_emitter(self, *args):
        socketio = args[0]
        while True:
            # one loop every second
            deltatime = 0
            socketio.sleep(1 - deltatime)
            if(self.isPlaying):
                begintime = perf_counter()

                for ambience in self.current_ambiences:
                    # music
                    ambience.music.track_playing_for += 1
                    current_track, is_new = ambience.music.get_curr_track()
                    if is_new:
                        name = current_track['name']
                        volume = current_track['volume'] *\
                            ambience.music.volume
                        socketio.emit('ambicall_music',
                                      {
                                          'name': f'{name}',
                                          'volume': f'{volume}'
                                      })

                    # sfx
                    sfx_this_tick = ambience.sfx.tick()
                    for sfx in sfx_this_tick:
                        name = sfx['name']
                        volume = sfx['real_volume']
                        socketio.emit('ambicall_sfx',
                                      {
                                          'name': f'{name}',
                                          'volume': f'{volume}'
                                      })

                endtime = perf_counter()
                deltatime = endtime - begintime

    def ambience_begin(self):
        self.isPlaying = True

    def ambience_stop(self, name):
        for ambience in self.current_ambiences:
            if ambience.name == name:
                self.current_ambiences.remove(ambience)
                break
        if len(self.current_ambiences) == 0:
            self.isPlaying = False

    def ambience_play(self, name):
        ambience = self.ambience_load(name)
        self.current_ambiences.append(ambience)
        self.ambience_begin()


def run(socketio):
    thread_lock = threading.Lock()
    global ambi_manager
    ambi_manager = AmbienceManager()

    # when a client connects, and no ambience_emitter is running
    # start one on the emitter_thread.
    @socketio.event
    def connect():
        global emitter_thread
        with thread_lock:
            if(emitter_thread is None):
                emitter_thread = socketio.\
                                    start_background_task(
                                        ambi_manager.ambience_emitter,
                                        socketio
                                    )
