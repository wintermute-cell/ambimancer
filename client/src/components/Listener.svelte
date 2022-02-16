<script>
    export let socket;
    export let room_uuid;

    // join the corresponding room to receive all broadcasts for that room.
    function joinRoom() {
        console.log(room_uuid);
        console.log(socket);
        socket.emit('join_room_request', {
            'room': room_uuid
        });
    }

    socket.on('connect', () => {
        joinRoom();
    })

    // TODO: benchmark this and maybe exchange for access frequency buffer
    class SfxBuffer {
        constructor(maxLength) {
            this.maxLength = maxLength;
            this.buffer = {};
            this.recency_list = [];
        }

        // try to add a file to the buffer.
        // returns true in case the file didn't
        // exist before.
        tryAdd(name) {
            if(name in this.buffer) {
                // file is already buffered
                // move filename to front
                const idx = this.recency_list.indexOf(name);
                if(idx > -1){
                    this.recency_list.splice(idx, 1);
                    this.recency_list.push(name);
                }
            }
            else {
                // file not yet buffered
                let file = new Audio('./audio/ogg/' + room_uuid + '/sfx/' + name);
                this.buffer[name] = file;
                if(this.buffer.length > this.maxLength) {
                    // remove 0th element, add new name to list
                    const old_name = this.recency_list.at(0);
                    delete this.buffer[old_name];
                    this.recency_list.splice(0, 1);
                    this.recency_list.push(name);
                }
            }
            return this.buffer[name];
        }
    }


    // contains all the currently playing audio.
    class AmbienceContainer {
        constructor() {
            this.ambiences = {}
        }

        // removes the complete ambience if there are no more audio files left.
        cleanUp(ambience_name){
            if (this.ambiences[ambience_name]['music'].length == 0
                && this.ambiences[ambience_name]['sfx'].length == 0){
                delete this.ambiences[ambience_name];
            }
        }

        addMusic(file, name, ambience_name){
            if(!(ambience_name in this.ambiences))
                this.ambiences[ambience_name] = {
                    'music': {},
                    'sfx': {}
                }
            this.ambiences[ambience_name]['music'][name] = file;
            file.addEventListener('ended', () => {
                delete this.ambiences[ambience_name]['music'][name];
                this.cleanUp(ambience_name);
            })
        }

        addSfx(file, name, ambience_name){
            if(!(ambience_name in this.ambiences))
                this.ambiences[ambience_name] = {
                    'music': {},
                    'sfx': {}
                }
            this.ambiences[ambience_name]['sfx'][name] = file;
            file.addEventListener('ended', () => {
                // This prevents an error if the ambience is removed
                // from the 'actives' list before all sounds finish.
                if (typeof this.ambiences[ambience_name] == 'undefined') return;

                delete this.ambiences[ambience_name]['sfx'][name];
                this.cleanUp(ambience_name);
            })
        }

        stopAmbience(ambience_name){
            // TODO: manage fading out of stopped ambiences.
            for (const [, file] of Object.
                entries(this.ambiences[ambience_name]['music'])) {
                file.pause();
            }
            for (const [, file] of Object.
                entries(this.ambiences[ambience_name]['sfx'])) {
                file.pause();
            }
            delete this.ambiences[ambience_name];
        }
    }

    let currently_playing_audio = new AmbienceContainer();

    let currMusic = new Audio();
    socket.on('ambicall_music', (data) => {
        console.log('MUS: ' + data['name'] + ' ' + data['volume']);
        let audFile = new Audio('./audio/ogg/' + room_uuid + '/music/' + data['name'])
        audFile.loop = false;
        audFile.volume = data['volume'];
        currMusic = null; // without this, the old audio file starts playing again aswell...
        currMusic = audFile;
        currently_playing_audio.addMusic(audFile, data['name'], data['ambience_name']);
        currMusic.play();
    });

    const sfxBuffer = new SfxBuffer(32);
    socket.on('ambicall_sfx', (data) => {
        console.log('SFX: ' + data['name'] + ' ' + data['volume']);
        let audFile = sfxBuffer.tryAdd(data['name'])
        // check if the file is already playing, if so, play a copy.
        if (audFile.paused || audFile.ended || audFile.currentTime < 0) {
            audFile = audFile.cloneNode();
        }
        audFile.volume = data['volume'];
        currently_playing_audio.addSfx(audFile, data['name'], data['ambience_name']);
        audFile.play();
    });

    export function stopAmbience(name){
        currently_playing_audio.stopAmbience(name);
    }

</script>
