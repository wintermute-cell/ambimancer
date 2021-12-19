<script>
      import {io} from 'socket.io-client'

      const socket = io.connect('http://127.0.0.1:5000/')

      socket.on('connect', () => {
            console.log('socket connected');
      });

      let motd = "";
      let currTime = 0;
      let currSFXTime = 0;

      function get_motd(){
            fetch("./motd")
                  .then(d => d.text())
                  .then(d => (motd = d));
      }

      let audFile = new Audio("./audio/ogg/test");
      let sfxFile = new Audio("./audio/ogg/sfx");
      const playMusic = () => {
            audFile.play();
      }
      const stopMusic = () => {
            audFile.stop();
      }
      const playSFX = () => {
            sfxFile.play();
      }
      const stopSFX = () => {
            sfxFile.stop();
      }

      const updateCurrTime = () => {
            currTime = audFile.currentTime;
            currSFXTime = sfxFile.currentTime;
      }
      setInterval(updateCurrTime, 100);
</script>

<h1>Music Time: {currTime}</h1>
<h1>SFX Time: {currSFXTime}</h1>
<button on:click={playMusic}>play music</button>
<button on:click={stopMusic}>stop music</button>
<button on:click={playSFX}>play</button>
<button on:click={stopSFX}>play</button>
