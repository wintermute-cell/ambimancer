<script>

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
