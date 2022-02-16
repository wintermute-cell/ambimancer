<script>
    import store_userdata from '../stores/store_userdata.js'

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
        store_userdata.update((data) => {
            data.uid = license;
            return data;
        });
        fetch("./rooms/create?license_type=dev&license_key=" + license)
            .then(response => {
                response.json()
                    .then(json => {
                        createError.textContent = ''
                        if(json['state'] === 'success') {
                            store_userdata.update((data) => {
                                data.room_uuid = json['uuid'];
                                return data;
                            });
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

<body class='style-background'>
    <div class="center-menu">
        <div class='center-menu-item'>
            <h1>Join Room</h1>
            <form on:submit|preventDefault={tryConnect}>
                <label for="room_uuid">Room ID:</label><br>
                <p class="form_error" bind:this={joinError}></p>
                <input type="text" id="room_uuid" name="room_uuid">
                <button type="submit">Connect</button>
            </form>
        </div>

        <div class='center-menu-item'>
            <h1>Create Room</h1>
            <form on:submit|preventDefault={tryCreate}>
                <label for="license_key">License Key:</label><br>
                <p class="form_error" bind:this={createError}></p>
                <input type="text" id="license_key" name="license_key">
                <button type="submit">Create</button>
            </form>
        </div>
    </div>
</body>

<style>
    body {
        padding: 4em;
    }

    .center-menu {
        margin: 0 auto;
        width: 20em;
        height: auto;
        background-color: #ECDCB1;
        text-align: center;
        padding: 3em;
        border-radius: 64px;

        color: #593631;
    }

    .center-menu .center-menu-item {
        margin-top: 2em;
        margin-bottom: 4em;
    }
    .center-menu .center-menu-item h1 {
        font-family: 'DejaVu Serif';
        margin-top: 1em;
        margin-bottom: 0.2em;
    }

    .center-menu form label {
        color: #A78440;
        font-variant: small-caps;
        font-weight: bold;
    }
    .center-menu form input[type=text] {
        width: 90%;
        border: solid 2px;
        border-radius: 12px;
        border-color: rgba(0,0,0,0);
        background-color: white;
        background-image: url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHhtbG5zOnhsaW5rPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5L3hsaW5rIiB2ZXJzaW9uPSIxLjEiIHdpZHRoPSIyNTYiIGhlaWdodD0iMjU2IiB2aWV3Qm94PSIwIDAgMjU2IDI1NiIgeG1sOnNwYWNlPSJwcmVzZXJ2ZSI+CjxkZXNjPkNyZWF0ZWQgd2l0aCBGYWJyaWMuanMgMS43LjIyPC9kZXNjPgo8ZGVmcz4KPC9kZWZzPgo8ZyB0cmFuc2Zvcm09InRyYW5zbGF0ZSgxMjggMTI4KSBzY2FsZSgwLjcyIDAuNzIpIiBzdHlsZT0iIj4KCTxnIHN0eWxlPSJzdHJva2U6IG5vbmU7IHN0cm9rZS13aWR0aDogMDsgc3Ryb2tlLWRhc2hhcnJheTogbm9uZTsgc3Ryb2tlLWxpbmVjYXA6IGJ1dHQ7IHN0cm9rZS1saW5lam9pbjogbWl0ZXI7IHN0cm9rZS1taXRlcmxpbWl0OiAxMDsgZmlsbDogbm9uZTsgZmlsbC1ydWxlOiBub256ZXJvOyBvcGFjaXR5OiAxOyIgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoLTE3NS4wNSAtMTc1LjA1MDAwMDAwMDAwMDA0KSBzY2FsZSgzLjg5IDMuODkpIiA+Cgk8cGF0aCBkPSJNIDgxLjAyNyA2LjIzNyBDIDcxLjgyNyAtMS44NzcgNTcuNzk1IC0yLjEwNSA0OC4zNiA1LjczNCBjIC0xMC42MTggOC44MjIgLTExLjk2NyAyNC4wMTUgLTQuMTE0IDM0LjQ5NyBMIDAuODIyIDgzLjY1NiBjIC0wLjU1MSAwLjU1MSAtMC41NTEgMS40NDQgMCAxLjk5NCBsIDMuMDkyIDMuMDkyIGMgMC41NTEgMC41NTEgMS40NDQgMC41NTEgMS45OTQgMCBsIDUuMjU0IC01LjI1NCBsIDEuNjg0IDEuNjg0IGwgNC40MTUgNC40MTUgYyAwLjU1MSAwLjU1MSAxLjQ0NCAwLjU1MSAxLjk5NCAwIGwgMy4wOTIgLTMuMDkyIGMgMC41NTEgLTAuNTUxIDAuNTUxIC0xLjQ0NCAwIC0xLjk5NCBsIC0zLjU2OSAtMy41NjkgbCA2Ljc1MSAtNi43NTEgbCAzLjU2OSAzLjU2OSBjIDAuNTUxIDAuNTUxIDEuNDQ0IDAuNTUxIDEuOTk0IDAgbCAzLjA5MiAtMy4wOTIgYyAwLjU1MSAtMC41NTEgMC41NTEgLTEuNDQ0IDAgLTEuOTk0IGwgLTQuNDE1IC00LjQxNSBsIC0xLjY4NCAtMS42ODQgbCAyMS4yNDggLTIxLjI0OCBjIDkuODY3IDcuMzkzIDIzLjkwOSA2LjYzMSAzMi44ODEgLTIuMzQxIEMgOTIuNDMxIDMyLjc1OCA5Mi4wMzYgMTUuOTQ1IDgxLjAyNyA2LjIzNyB6IE0gNzguNjI3IDM2LjA5MyBjIC03LjI1IDkuMzQxIC0yMS4yMDQgOS4zNDEgLTI4LjQ1NCAwIGMgLTQuOTQgLTYuMzY1IC00Ljk0IC0xNS40OTQgMCAtMjEuODU5IGMgNy4yNSAtOS4zNDEgMjEuMjA0IC05LjM0MiAyOC40NTQgMCBDIDgzLjU2NyAyMC41OTggODMuNTY3IDI5LjcyOCA3OC42MjcgMzYuMDkzIHoiIHN0eWxlPSJzdHJva2U6IG5vbmU7IHN0cm9rZS13aWR0aDogMTsgc3Ryb2tlLWRhc2hhcnJheTogbm9uZTsgc3Ryb2tlLWxpbmVjYXA6IGJ1dHQ7IHN0cm9rZS1saW5lam9pbjogbWl0ZXI7IHN0cm9rZS1taXRlcmxpbWl0OiAxMDsgZmlsbDogcmdiKDEzMCwxMzAsMTMwKTsgZmlsbC1ydWxlOiBub256ZXJvOyBvcGFjaXR5OiAxOyIgdHJhbnNmb3JtPSIgbWF0cml4KDEgMCAwIDEgMCAwKSAiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgLz4KPC9nPgo8L2c+Cjwvc3ZnPg==');
        background-position: 10px 10px;
        background-repeat: no-repeat;
        background-size: 1em;
        padding-left: 40px;
    }
    .center-menu form input[type=text]:focus {
        box-shadow: 4px 4px 3px grey;
        border: solid 2px;
        border-color: #A78440;
        outline: none;
    }
    .center-menu form button {
        color: white;
        padding: 0.8em;
        border: solid 2px;
        border-radius: 12px;
        border-color: #CA9064;
        outline: none;
        background-color: #CA9064;
        font-weight: bold;
    }
    .center-menu form button:hover {
        border: solid 2px;
        border-color: #A78440;
    }


    @media only screen and (max-width: 550px) {
        .center-menu {
            width: 70%;
        }

    }
</style>
