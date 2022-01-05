<script>
      export let socket;
      export let ambience_name = '';

      $: if(ambience_name !== '') {
            loadAmbienceJson(ambience_name);
      };

      const sendTest = () => {
            socket.emit('ambience_edit', {
                  ambience: 'test',
                  type: 'music'
            });
      }

      function loadAmbienceJson(ambience_name) {
            fetch('./ambience/read?uid=dev_key&ambience_name=' + ambience_name)
                  .then(response => {
                        response.json()
                              .then(json => {
                                    console.log(json);
                              })
                  })
      }

      function writeAmbienceJson(ambience_name) {
            // TODO: generate a "json-diff"-like string, to send minimal amount of data back to the server. The server can then also use that data to determine if a live-edit is necessary.
      }
</script>

<div class="main-container">
      <button on:click={sendTest}>Test To Server</button>
</div>

<style>
      .main-container {
            margin: 1em;
            margin-top: 2.5em;
      }
</style>
