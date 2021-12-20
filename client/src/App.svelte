<script>
      import {io} from 'socket.io-client'

      const socket = io.connect('http://127.0.0.1:5000/')

      socket.on('ambicall_music', (data) => {
            console.log('MUS:')
            console.log(data['name']);
            console.log(data['volume'])
            let audFile = new Audio('./audio/ogg/music/' + data['name'])
            audFile.volume = data['volume']
            audFile.play()
      });

      socket.on('ambicall_sfx', (data) => {
            console.log('SFX:')
            console.log(data['name']);
            console.log(data['volume'])
            let audFile = new Audio('./audio/ogg/sfx/' + data['name'])
            audFile.volume = data['volume']
            audFile.play()
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

      const playMus = () => {
            fetch("./control/play/test")
      }
      const stopMus = () => {
            fetch("./control/stop/test")
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

<button on:click={playMus}>ambiplay</button>
<button on:click={stopMus}>ambistop</button>
