<script>
      import MasterControl from './MasterControl.svelte';
      import AmbienceEditor from './AmbienceEditor.svelte'

      // connect to the server.
      // TODO: get correct server ip from another service.
      import {io} from 'socket.io-client';
      const socket = io.connect('http://127.0.0.1:5000/');

      // TODO: remove for deployment.
      socket.on('debug', (data) => {
            console.log(data['msg']);
      });

      let hovering = false;
      let containers = {
            'active': [
                        'ambi1',
                        'ambi2',
            ],
            'all': [
                        'ambi3',
                        'ambi4',
                        'ambi5',
                        'ambi6',
                        'ambi7',
                        'ambi8',
                        'ambi9',
                        'ambi10',
                        'ambi11',
                        'ambi12'
            ]
      }
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
                  //TODO: send call to server to start streaming the ambience
                  } else if (new_container_name === 'all') {
                        //TODO: send call to server to stop streaming the ambience
            }
      };

      let selected_ambience = '';
      function select_ambience(event) {
            selected_ambience = event.target.id;
      }
</script>

<div class="grid-container">
      <div class="grid-item"
           id="panel_active"
           on:drop|preventDefault={event => drop(event, 'active')}
           ondragover="return false"
           on:dragenter="{() => hovering = 'active'}"
           on:dragleave="{() => hovering = null}"
           class:hovering="{hovering === 'active'}"
      >
            <div class="grid-container-title">Active Ambiences</div>
            <ul class="ambience-list">
                  {#each containers['active'] as item,i}
                        <li draggable={true}
                              on:dragstart={event => dragstart(event, 'active', i)}
                              on:click={select_ambience}
                              id={item}
                              class="ambience-list-item"
                        >
                              {item}
                        </li>
                  {/each}
            </ul>
      </div>
      <div class="grid-item"
           id="panel_all"
           on:drop|preventDefault={event => drop(event, 'all')}
           ondragover="return false"
           on:dragenter="{() => hovering = 'all'}"
           on:dragleave="{() => hovering = null}"
           class:hovering="{hovering === 'all'}"
      >
            <div class="grid-container-title">All Ambiences</div>
            <div class="ambience-list">
                  {#each containers['all'] as item,i}
                        <div draggable={true}
                              on:dragstart={event => dragstart(event, 'all', i)}
                              on:click={select_ambience}
                              id={item}
                              class="ambience-list-item"
                        >
                              {item}
                        </div>
                  {/each}
            </div>
      </div>
      <div class="grid-item" id="panel_editor">
            <div class="grid-container-title">Editor</div>
            <AmbienceEditor socket={socket} ambience_name={selected_ambience}/>
      </div>
</div>

<!--
<MasterControl socket={socket} />
<AmbienceEditor socket={socket} />
-->

<style>
      .ambience-list-item {
            display: block;
            width: 4em;
            height: 4em;
            border: 2px solid;
            margin: 1em;
      }
      .ambience-list {
            width: 100%;
            display: flex;
            flex-wrap: wrap;
            margin: 0px;
            margin-top: 1.5em;
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
            background-color: #eb8034;
            padding: 10px;
            box-sizing: border-box;
      }
      .grid-container > div {
            background-color: #e8a16f;
            overflow: auto;
      }
      .grid-container-title {
            text-align: left;
            vertical-align: top;
            font-size: 1em;
            position: fixed;
            background-color: #eb8034;
            padding: 4px;
      }
      #panel_active {
            grid-area: active;
      }
      #panel_all {
            grid-area: all;
      }
</style>
