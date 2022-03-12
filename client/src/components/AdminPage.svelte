<script>
    import AmbienceEditor from './AmbienceEditor.svelte'
    import store_userdata from '../stores/store_userdata.js';

    import Listener from './Listener.svelte';
    let listener;

    // connect to the server.
    // TODO: get correct server ip from another service.
    import {io} from 'socket.io-client';
    const socket = io.connect('http://127.0.0.1:5000/');



    let uid;
    let room_uuid;
    store_userdata.subscribe((data) => {
        uid = data.uid;
        room_uuid = data.room_uuid;
    });

    let hovering = false;
    let containers = {
        'active': [],
        'all': []
    }

    function getAmbienceNames(){
        fetch('./ambience/list?uid=dev_key')
            .then(response => {
                response.json()
                    .then(json => {
                        console.log(json)
                        for (const name of json['ambience_names']) {
                            console.log(name)
                            containers['all'].push({
                                name: name,
                                active: false
                            })
                            // trigger svelte reactivity through assignment
                            containers['all'] = containers['all']
                        }
                    })
            });
    }

    getAmbienceNames();
    console.log(containers)

    function createNewAmbience() {

    }

    // music track drag and drop
    function dragstart(event, container_name, item_idx) {
        event.dataTransfer.effectAllowed = 'move';
        event.dataTransfer.dropEffect = 'move';
        let obj = {
            container_name: container_name,
            item_idx: item_idx,
            id: event.target.getAttribute('id')
        };
        event.dataTransfer.setData('text/plain', JSON.stringify(obj));
    };
    function drop(event, new_container_name) {
        event.dataTransfer.dropEffect = 'move';
        let json_obj = event.dataTransfer.getData('text/plain');
        let obj = JSON.parse(json_obj);
        let item_idx = obj.item_idx;
        let old_container_name = obj.container_name;
        const item = containers[old_container_name].splice(item_idx,1)[0];
        containers[new_container_name] = [...containers[new_container_name],item];
        hovering = null;
        if (new_container_name === 'active') {
            item.active = true;
            socket.emit('ambience_set_active', {
                uid: uid,
                ambience_name: item.name
            });
        } else if (new_container_name === 'all') {
            item.active = false;
            socket.emit('ambience_set_inactive', {
                uid: uid,
                ambience_name: item.name
            });
            listener.stopAmbience(item.name);
        }
    };

    // activating ambience for editor
    let selected_ambience = '';
    let selected_ambience_is_active;
    function select_ambience(event) {
        selected_ambience_is_active =
            event.target.classList.contains('active-ambience') ? true : false;
        selected_ambience = event.target.id;
    }
</script>

<div class="grid-container">
    <!--
    ACTIVE AMBIENCES PANEL
    -->
    <div class="grid-item style-background"
         id="panel_active"
         on:drop|preventDefault={event => drop(event, 'active')}
         ondragover="return false"
         on:dragenter="{() => hovering = 'active'}"
         on:dragleave="{() => hovering = null}"
         class:hovering="{hovering === 'active'}"
         >
         <div class="grid-container-title">Active Ambiences</div>
         <div class="ambience-list">
             {#each containers['active'] as item,i}
                 <div draggable={true}
                     on:dragstart={event => dragstart(event, 'active', i)}
                     on:click={select_ambience}
                     id={item.name}
                     class="ambience-list-item active-ambience"
                     >
                     {item.name}, {item.active}
                 </div>
             {/each}
         </div>
    </div>

    <!--
    INACTIVE AMBIENCES PANEL
    -->
    <div class="grid-item style-background"
         id="panel_all"
         on:drop|preventDefault={event => drop(event, 'all')}
         ondragover="return false"
         on:dragenter="{() => hovering = 'all'}"
         on:dragleave="{() => hovering = null}"
         class:hovering="{hovering === 'all'}"
         >
         <div class="grid-container-title">All Ambiences</div>
         <div class="grid-container-buttons">
             <button onclick={() => {createNewAmbience()}}>+</button>
         </div>
         <div class="ambience-list">
             {#each containers['all'] as item,i}
                 <div draggable={true}
                      on:dragstart={event => dragstart(event, 'all', i)}
                      on:click={select_ambience}
                      id={item.name}
                      class="ambience-list-item"
                      >
                      {item.name}, {item.active}
                 </div>
             {/each}
         </div>
    </div>

    <!--
    EDITOR PANEL
    -->
    <div class="grid-item style-background" id="panel_editor">
        <div class="grid-container-title">Editor</div>
        <AmbienceEditor socket={socket}
                        ambience_name={selected_ambience}
                        is_active={selected_ambience_is_active}
                        />
    </div>
</div>

<Listener bind:this={listener} socket={socket} room_uuid={room_uuid} />
<!--
    <MasterControl socket={socket} />
    <AmbienceEditor socket={socket} />
-->

<style>
     .ambience-list-item {
        background-color: #926B48;
        border: outset 3px lightgray;
        border-radius: 16px;
        box-shadow: 6px 6px 16px rgba(0,0,0,0.46), inset 0 0 12px rgba(0,0,0,0.5);
        padding: 1.2em;
        margin: 1em;
        font-family: 'Open Sans';
        font-weight: bold;
        color: white;
        width: 4em;
        height: 4em;
    }
    .ambience-list-item:hover {
        background-color: #a37750;
    }
    .ambience-list-item:active {
        color: #ebebeb;
        background-color: #876241;
        box-shadow: 3px 3px 10px rgba(0,0,0,0.46), inset 0 0 12px rgba(0,0,0,0.5);
    }
    .ambience-list {
        width: 100%;
        display: flex;
        flex-wrap: wrap;
        margin: 0px;
        margin-top: 2.2em;
        padding: 0px;
    }
    .grid-container {
        height: 100%;
        width: 100%;
        grid-template-areas:
            'active editor'
            'all all';
            grid-template-rows: auto 40%;
            grid-template-columns: 20em auto;
            grid-gap: 10px;
            background-color: #A78440;
            padding: 10px;
            box-sizing: border-box;
    }
    .grid-container > div {
        overflow: auto;
        scrollbar-width: none; /* Disable scrollbar on firefox */
        -ms-overflow-style: none;  /* Internet Explorer 10+ */
    }
    .grid-container > div::-webkit-scrollbar {
        display: none;  /* Safari and Chrome */
    }
    .grid-container-title {
        font-family: 'Open Sans';
        font-weight: bold;
        text-align: left;
        vertical-align: top;
        font-size: 1em;
        position: fixed;
        background-color: #A78440;
        padding: 0.6em;
        padding-top: 0.2em;
        box-shadow: 10px 10px 16px -6px rgba(1, 1, 1, 0.6);
    }
    .grid-container-buttons {
        margin-left: 10em;
        height: 1.8em;
        font-family: 'Open Sans';
        font-weight: bold;
        text-align: left;
        vertical-align: top;
        font-size: 1em;
        position: fixed;
        background-color: #A78440;
        box-shadow: 10px 10px 16px -6px rgba(1, 1, 1, 0.6);
    }
    .grid-container-buttons button {
        color: white;
        font-size: 1em;
        width: 2em;
        border: none;
        background-color: #A78440;
        box-shadow: 10px 10px 16px -6px rgba(1, 1, 1, 0.6);
    }
    .grid-item {
        border-radius: 30px;
        box-shadow: inset 0 0 16px rgba(1, 1, 1, 0.6);
    }
    #panel_active {
        grid-area: active;
    }
    #panel_all {
        grid-area: all;
    }

    @media only screen and (max-width: 800px), (max-height: 620px) {
        .grid-container {
            grid-template-areas:
                'active active'
                'all all';
        }
        #panel_editor {
            display: none;
        }
    }
</style>
