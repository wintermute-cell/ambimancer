<script>
    import { Tabs, TabList, TabPanel, Tab } from './tabs/tabs.js';
    import RangeSlider from "svelte-range-slider-pips";
    import store_userdata from '../stores/store_userdata.js';
    import Modal from './Modal.svelte'

    export let socket;
    export let ambience_name = '';
    export let is_active;

    let uid;
    store_userdata.subscribe((data) => {
        uid = data.uid;
    });


    $: if(ambience_name !== '') {
        loadAmbienceJson(ambience_name);
    };


    // the corresponding checkboxes are bound to these.
    // the binding is used to enable them to toggle each other.
    let mus_crossfade_checkbox;
    let mus_pause_checkbox;

    let current_ambience = null;
    function loadAmbienceJson(ambience_name) {
        fetch('./ambience/read?uid=dev_key&ambience_name=' + ambience_name)
            .then(response => {
                response.json()
                    .then(json => {
                        current_ambience = json;
                    })
            });
    }

    // sends a message about the change back to the server to apply to the json.
    async function writeAmbienceJson(target_string, new_val, to_disk = true) {
        await new Promise(cb => setTimeout(cb, 1)); // seems to be required for the function to run asyncronously.
        socket.emit('ambience_edit', {
            uid: uid,
            to_disk: to_disk,
            ambience_name: current_ambience.name,
            target: target_string,
            new_val: new_val
        });
    }

    // list drag and drop reorder
    let hovering;
    let sliding = false;
    const drop = (event, target) => {
        event.dataTransfer.dropEffect = 'move';
        const start = parseInt(event.dataTransfer.getData('text/plain'));
        const newTrackList = current_ambience.music.tracks;

        if (start < target) {
            newTrackList.splice(target + 1, 0, newTrackList[start]);
            newTrackList.splice(start, 1);
        } else {
            newTrackList.splice(target, 0, newTrackList[start]);
            newTrackList.splice(start + 1, 1);
        }
        current_ambience.music.tracks = newTrackList;
        writeAmbienceJson('reorder_music_track', [start, target])
        hovering = null;
    }
    const dragStart = (event, i) => {
        event.dataTransfer.effectAllowed = 'move';
        event.dataTransfer.dropEffect = 'move';
        const start = i;
        event.dataTransfer.setData('text/plain', start);
    }

    // sfx editor
    let active_sfx_layer_idx = null;

    // file selection for new tracks
    let fileselectorOpen = false;
    let filetype = '';
    const chooseFile = (type) => {
        if (type === 'music') {
            fileselectorOpen = true;
            filetype = type;
        } else if (type === 'sfx') {
            fileselectorOpen = true;
            filetype = type;
        }
    }
    let TESTavailablefiles = [
        'filename1',
        'filename2',
        'filename3',
        'filename4',
        'filename5',
        'filename1',
        'filename1',
        'filename1',
        'filename2',
        'filename3',
        'filename4',
        'filename5',
        'filename2',
        'filename3',
        'filename4',
        'filename5',
        'filename2',
        'filename3',
        'filename4',
        'filename5'
    ]
</script>

<Modal bind:isOpen={fileselectorOpen}>
    <div slot='header'>
      <h3>Choose a Track</h3>
    </div>
    <div slot='content'>
        <ul>
            {#each TESTavailablefiles as file}
                <div>
                    {file}
                </div>
            {/each}
        </ul>
    </div>
    <div slot='footer'>

    </div>
</Modal>

<div class="main-container">
    {#if current_ambience != null}
        <h2>{current_ambience.name}</h2>
        <Tabs>
            <TabList>
                <Tab>Music</Tab>
                <Tab>SFX</Tab>
            </TabList>

            <TabPanel>
                <div class="music-grid-container">
                    <div class="grid-item" id="music-panel-tracklist">
                        <ul>
                            {#each current_ambience.music.tracks as track, index}
                                <div
                                    class='track-list-item'
                                    draggable={!sliding}
                                    on:dragstart|self={event => dragStart(event, index)}
                                    on:drop|preventDefault={event => drop(event, index)}
                                    ondragover='return false'
                                    on:dragenter|self={() => hovering = index}
                                    class:is-active={hovering === index}
                                    >
                                    {index}
                                    <button on:click={() => {chooseFile('music')}}>
                                        {track.name}
                                    </button>
                                    <div class="track-list-item-slider">
                                        <RangeSlider
                                            id="volume-slider"
                                            values={[track.volume]}
                                            min={0} max={1} float step={0.05}
                                            springValues={{stiffness:0.3, damping:1}}
                                            on:start={() => {
                                                sliding = true;
                                            }}
                                            on:change={(e) => {
                                                if(is_active){
                                                    track.volume = e.detail.value;
                                                    writeAmbienceJson(`music.tracks.${track.name}.volume`, e.detail.value, false);
                                            }
                                            }}
                                            on:stop={(e) => {
                                                sliding = false;
                                                writeAmbienceJson(`music.tracks.${track.name}.volume`, e.detail.value);
                                            }}
                                            />
                                    </div>
                                </div>
                            {/each}
                        </ul>
                    </div>

                    <div class="grid-item" id="music-panel-settings">
                        <label class="settings-label" for="g-music-vol">General Volume
                            <RangeSlider
                                id="g-music-vol"
                                values={[current_ambience.music.volume]}
                                min={0} max={1} float step={0.05}
                                springValues={{stiffness:0.3, damping:1}}
                                on:change={(e) => {
                                    if(is_active){
                                        current_ambience.music.volume = e.detail.value;
                                        writeAmbienceJson('music.volume', e.detail.value, false);
                                }
                                }}
                                on:stop={(e) => {
                                    writeAmbienceJson('music.volume', e.detail.value);
                                }}
                                />
                        </label>
                        <label class="settings-label">Shuffle
                            <input type="checkbox"
                                   checked={!!current_ambience.music.shuffle}
                                   on:change={(e) => {
                                       const checked_num = e.target.checked ? 1 : 0;
                                       current_ambience.music.shuffle = checked_num;
                                       writeAmbienceJson('music.shuffle', checked_num);
                                   }}
                                   />
                        </label>
                        <label class="settings-label">Crossfade
                            <input type="checkbox"
                                   bind:this={mus_crossfade_checkbox}
                                   checked={!!current_ambience.music.crossfade.active}
                                   on:change={(e) => {
                                   const checked_num = e.target.checked ? 1 : 0;
                                   current_ambience.music.crossfade.active = checked_num;
                                   writeAmbienceJson('music.crossfade.active', checked_num);
                                   if (!!current_ambience.music.pause.active){
                                   mus_pause_checkbox.checked = false;
                                   current_ambience.music.pause.active = 0;
                                   writeAmbienceJson('music.pause.active', 0);
                                   }
                                   }}
                            />
                            {#if !!current_ambience.music.crossfade.active}
                                <input type="number"
                                       value={current_ambience.music.crossfade.by_secs}
                                       on:change={(e) => {
                                       current_ambience.music.crossfade.by_secs = e.target.value;
                                       writeAmbienceJson('music.crossfade.by_secs', parseFloat(e.target.value));
                                       }}
                                       />
                            {/if}
                        </label>
                        <label class="settings-label">Pause
                            <input type="checkbox"
                                   bind:this={mus_pause_checkbox}
                                   checked={!!current_ambience.music.pause.active}
                                   on:change={(e) => {
                                   const checked_num = e.target.checked ? 1 : 0;
                                   current_ambience.music.pause.active = checked_num;
                                   writeAmbienceJson('music.pause.active', checked_num);
                                   if (!!current_ambience.music.crossfade.active){
                                   mus_crossfade_checkbox.checked = false;
                                   current_ambience.music.crossfade.active = 0;
                                   writeAmbienceJson('music.crossfade.active', 0);
                                   }
                                   }}
                            />
                            {#if !!current_ambience.music.pause.active}
                                <input type="number"
                                       value={current_ambience.music.pause.by_secs}
                                       on:change={(e) => {
                                       current_ambience.music.pause.by_secs = e.target.value;
                                       writeAmbienceJson('music.pause.by_secs', parseFloat(e.target.value));
                                       }}
                                       />
                            {/if}
                        </label>
                    </div>
                </div>
            </TabPanel>
            <TabPanel>
                <div class="sfx-grid-container">
                    <div class="grid-item" id="sfx-panel-layerlist">
                        {#each current_ambience.sfx.layers as layer, index}
                            <div class='sfx-layer-list-item'
                                 on:click|self={(e) => {
                                     active_sfx_layer_idx = index;
                                 }}
                                 >
                                {index}
                                <input type="text" placeholder={layer.name}>
                                <div class="sfx-layer-list-item-slider" >
                                    <RangeSlider
                                        id="sfx-layer-vol"
                                        values={[layer.volume]}
                                        min={0} max={1} float step={0.05}
                                        springValues={{stiffness:0.3, damping:1}}
                                        on:change={(e) => {
                                        if(is_active){
                                        layer.volume = e.detail.value;
                                        writeAmbienceJson(`sfx.layers.${layer.name}.volume`, e.detail.value, false);
                                        }
                                        }}
                                        on:stop={(e) => {
                                        sliding = false;
                                        writeAmbienceJson(`sfx.layers.${layer.name}.volume`, e.detail.value);
                                        }}
                                        />
                                    <!-- TODO: Maybe add toggle to set interval to minutes instead of seconds-->
                                    <RangeSlider
                                        id="sfx-layer-interval"
                                        values={layer.interval}
                                        range
                                        pushy
                                        min={0} max={120} float step={1}
                                        springValues={{stiffness:0.3, damping:1}}
                                        on:change={(e) => {
                                        if(is_active){
                                        layer.interval = e.detail.values;
                                        writeAmbienceJson(`sfx.layers.${layer.name}.interval`, e.detail.values, false);
                                        }
                                        }}
                                        on:stop={(e) => {
                                        sliding = false;
                                        writeAmbienceJson(`sfx.layers.${layer.name}.interval`, e.detail.values);
                                        }}
                                        />
                                </div>
                            </div>
                        {/each}
                    </div>

                    <div class="grid-item" id="sfx-panel-tracklist">
                        {#if active_sfx_layer_idx != null}
                        {#each current_ambience.sfx.layers[active_sfx_layer_idx].tracks as track, index}
                            <div class='track-list-item'>
                                {index}
                                <button on:click={() => {chooseFile('sfx')}}>
                                    {track.name}
                                </button>
                                <div class="track-list-item-slider">
                                    <div>
                                        V
                                    </div>
                                    <RangeSlider
                                        id="volume-slider"
                                        values={[track.volume]}
                                        min={0} max={1} float step={0.05}
                                        springValues={{stiffness:0.3, damping:1}}
                                        on:change={(e) => {
                                        if(is_active){
                                        track.volume = e.detail.value;
                                        writeAmbienceJson(`sfx.layers.${current_ambience.sfx.layers[active_sfx_layer_idx].name}.tracks.${track.name}.volume`, e.detail.value, false);
                                        }
                                        }}
                                        on:stop={(e) => {
                                        sliding = false;
                                        writeAmbienceJson(`sfx.layers.${current_ambience.sfx.layers[active_sfx_layer_idx].name}.tracks.${track.name}.volume`, e.detail.value);
                                        }}
                                        />
                                </div>
                                <div class="track-list-item-slider">
                                    <div>
                                        C
                                    </div>
                                    <RangeSlider
                                        id="volume-slider"
                                        values={[track.chance]}
                                        min={0} max={1} float step={0.05}
                                        springValues={{stiffness:0.3, damping:1}}
                                        on:start={() => {
                                        sliding = true;
                                        }}
                                        on:change={(e) => {
                                        if(is_active){
                                        track.chance = e.detail.value;
                                        writeAmbienceJson(`sfx.layers.${current_ambience.sfx.layers[active_sfx_layer_idx].name}.tracks.${track.name}.chance`, e.detail.value, false);
                                        }
                                        }}
                                        on:stop={(e) => {
                                        sliding = false;
                                        writeAmbienceJson(`sfx.layers.${current_ambience.sfx.layers[active_sfx_layer_idx].name}.tracks.${track.name}.chance`, e.detail.value);
                                        }}
                                        />
                                </div>
                            </div>
                        {/each}
                        {/if}
                    </div>
                </div>
            </TabPanel>
        </Tabs>
    {/if}
</div>

<style>
    .main-container {
        margin: 1em;
        margin-top: 2.5em;
    }

    .music-grid-container {
        display: grid;
        grid-template-areas:
            'list settings';
        grid-template-columns: 60% auto;
    }
    #music-panel-tracklist {
        grid-area: list;
        overflow: scroll;
        overflow: hidden;
    }
    #music-panel-settings {
        grid-area: settings;
    }

    .sfx-grid-container {
        display: grid;
        grid-template-areas:
            'layer tracks';
        grid-template-columns: 50% auto;
    }
    #sfx-panel-layerlist {
        grid-area: layer;
        overflow: scroll;
        overflow: hidden;
    }
    #sfx-panel-tracklist {
        grid-area: tracks;
        overflow: scroll;
        overflow: hidden;
    }

    .track-list-item {
        text-align: center;
        display: flex;
        width: 42em;
        padding: 0.5em 1em;
        border-style: outset;
        border-color: #EB8034;
        border-radius: 4px;
        margin: 0.5em;
    }
    .track-list-item-slider {
        width: 12em;
    }

    .sfx-layer-list-item {
        margin: 0.5em;
        border-left: outset;
        border-bottom: outset;
        border-top: outset;
        border-left: outset;
        border-color: #EB8034;
        border-radius: 4px;
        border-top-right-radius: 0px;
        border-bottom-right-radius: 0px;
    }
</style>
