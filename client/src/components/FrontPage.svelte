<script>
      // functions to transfer to the views.
      export let createRoomFunc = () => {};
      export let joinRoomFunc = () => {};

      let joinError;
      let createError;


      const tryConnect = (e) => {
            const formData = new FormData(e.target);
            let uuid = formData.get('room_uuid');
            console.log("Not implemented!");
            //TODO: room finding system goes here.
            joinRoomFunc();
      };

      const tryCreate = (e) => {
            const formData = new FormData(e.target);
            let license = formData.get('license_key');
            fetch("./rooms/create?license_type=dev&license_key=" + license)
                  .then(response => {
                        response.json()
                              .then(json => {
                                    createError.textContent = ''
                                    if(json['state'] === 'success') {
                                          createRoomFunc();
                                    }
                                    else if (json['state'] === 'bad_license') {
                                          createError.textContent = 'Invalid Key!';
                                    }
                                    else {

                                    }
                              });
                  });
      };

</script>

<h1>Join Room</h1>
<form on:submit|preventDefault={tryConnect}>
      <label for="room_uuid">Room ID:</label><br>
      <input type="text" id="room_uuid" name="room_uuid">
      <button type="submit">Connect</button>
      <p class="form_error" bind:this={joinError}></p>
</form>

<h1>Create Room</h1>
<form on:submit|preventDefault={tryCreate}>
      <label for="license_key">License Key:</label><br>
      <input type="text" id="license_key" name="license_key">
      <button type="submit">Create</button>
      <p class="form_error" bind:this={createError}></p>
</form>
