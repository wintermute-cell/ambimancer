<script>
      let motd = ""

      function get_motd(){
            fetch(./motd)
                  .then(d => d.text())
                  .then(d => (motd = d));
      }
</script>

<h1>MOTD: {motd}</h1>
      <button on:click={get_motd}>refresh</button>
