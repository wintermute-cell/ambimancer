<script>
      export let socket;

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
                        let file = new Audio('./audio/ogg/sfx/' + name);
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

      // TODO: make this adjustable in interface
      const sfxBuffer = new SfxBuffer(16);
      let currMusic = new Audio();

      socket.on('ambicall_music', (data) => {
            console.log('MUS: ' + data['name'] + ' ' + data['volume']);
            let audFile = new Audio('./audio/ogg/music/' + data['name'])
            audFile.loop = false;
            audFile.volume = data['volume'];
            currMusic = null; // without this, the old audio file starts playing again aswell...
            currMusic = audFile;
            currMusic.play();
      });

      socket.on('ambicall_sfx', (data) => {
            console.log('SFX: ' + data['name'] + ' ' + data['volume']);
            let audFile = sfxBuffer.tryAdd(data['name'])
            audFile.volume = data['volume'];
            audFile.play();
      });

      const playMus = () => {
            fetch("./control/play/test");
      }
      const stopMus = () => {
            if(currMusic) {
                  fetch("./control/stop/test");
                  currMusic.pause();
                  currMusic = null;
            }
      }

      socket.on('disconnect', () => {
            stopMus();
      });

//      const updateCurrTime = () => {
//            currTime = audFile.currentTime;
//            currSFXTime = sfxFile.currentTime;
//      }
//      setInterval(updateCurrTime, 100);
</script>

<button on:click={playMus}>Start Ambience Emitter</button>
<button on:click={stopMus}>Stop Ambience Emitter</button>
