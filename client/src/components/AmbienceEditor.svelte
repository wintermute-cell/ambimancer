<script>
      export let socket;

      const sendTest = () => {
            socket.emit('ambience_edit', {
                  ambience: 'test',
                  type: 'music'
            });
      }
</script>

<button on:click={sendTest}>Test To Server</button>
