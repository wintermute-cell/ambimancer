<script>
      import MasterControl from './MasterControl.svelte';
      import AmbienceEditor from './AmbienceEditor.svelte'

      import {io} from 'socket.io-client';
      const socket = io.connect('http://127.0.0.1:5000/');

      socket.on('debug', (data) => {
            console.log(data['msg']);
      });
</script>

<MasterControl socket={socket} />
<AmbienceEditor socket={socket} />
