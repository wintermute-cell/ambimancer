<script>
    import { Tabs, TabList, TabPanel, Tab } from './tabs/tabs.js';
    import RangeSlider from "svelte-range-slider-pips";
    import store_userdata from '../stores/store_userdata.js';
    import Modal from './Modal.svelte'

    export let socket;
    export let ambience_name = '';
    export let is_active; // describes if the edited ambience is currently playing.

    let uid;
    let room_uuid;
    store_userdata.subscribe((data) => {
        uid = data.uid;
        room_uuid = data.room_uuid;
    });


    $: if(ambience_name !== '') {
        loadAmbienceJson(ambience_name);
    };

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

    // the corresponding checkboxes are bound to these.
    // the binding is used to enable them to toggle each other.
    let mus_crossfade_checkbox;
    let mus_pause_checkbox;

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

    // REMOVING TRACKS AND LAYERS FROM THE CURRENT AMBIENCE
    // removing music tracks
    function rm_music_track(index) {
        current_ambience.music.tracks.splice(index, 1);
        current_ambience = current_ambience // trigger reactivity
        writeAmbienceJson(`rm.music.${index}`, '');
    }
    // removing sfx tracks
    function rm_sfx_track(track_index, layer_index) {
        current_ambience.sfx.layers[layer_index].tracks.splice(track_index, 1);
        current_ambience = current_ambience // trigger reactivity
        writeAmbienceJson(`rm.sfx.${layer_index}.${track_index}`, '');
    }
    // removing sfx layers


    // sfx editor
    let active_sfx_layer_idx = null;
    let chanceSliderValues = [];
    let currentSlidingIndex = -1; // the idx of the chance slider the user is currently interacting with, used to prevent the below function from setting that sliders value
    $: {
        if(active_sfx_layer_idx != null && current_ambience != null){
            let i = 0;
            for (i = 0; i < chanceSliderValues.length; i++) {
                if(!(typeof current_ambience.sfx.layers[active_sfx_layer_idx].tracks[i] === 'undefined')){
                    if(i == currentSlidingIndex){
                        continue;
                    }
                    chanceSliderValues[i] = [
                        current_ambience.sfx.
                        layers[active_sfx_layer_idx].
                        tracks[i].chance
                    ];
                }
            }
            // fill one slot more with a 0 value, this prevents erroring
            // when a new track is eventually inserted an tries to lookup this slot.
            chanceSliderValues[i+1] = [0];
        }
    }
    // This function shifts the chances of all tracks in a layer when one of them
    // changes, or is inserted as a new one (ergo, changes from 0->x).
    // It then returns the chance of the changed track back.
    function recalcChances(new_chance, track_idx=null){
        let curr_tracks = current_ambience.sfx.layers[active_sfx_layer_idx].tracks;

        // percentage that the other tracks, beside the changed one,
        // took, summed together, before and after the change.
        let old_perc = track_idx != null ? 1 - curr_tracks[track_idx].chance : 1;
        let new_perc = 1 - new_chance;

        // percentages of the other tracks.
        for (let i = 0; i < curr_tracks.length; i++) {
            let old_percentage = curr_tracks[i].chance/old_perc;
            current_ambience.sfx.layers[active_sfx_layer_idx].tracks[i].chance =
                new_perc * old_percentage;
        }

        return new_chance;
    }

    // file selection for new tracks
    let filenamesMusic = []
    let filenamesSfx = []
    function getFilenames(type) {
        if (type === 'music') {
            fetch('./audio/getfilenames?type=music&room=' + room_uuid)
                .then(response => {
                    response.json()
                        .then(json => {
                            filenamesMusic = json.names;
                        })
                });
        }
        else if (type === 'sfx'){
            fetch('./audio/getfilenames?type=sfx&room=' + room_uuid)
                .then(response => {
                    response.json()
                        .then(json => {
                            filenamesSfx = json.names;
                        })
                });

        }
        else {
            console.log('ERROR: tried to run "getFilenames()" for an invalid type!');
        }
    }
    let fileselectorOpen = false;
    let fileSelectorType = '';
    const chooseFile = (type) => {
        getFilenames(type);
        if (type === 'music') {
            fileselectorOpen = true;
            fileSelectorType = type;
        } else if (type === 'sfx') {
            fileselectorOpen = true;
            fileSelectorType = type;
        }
    }
    function uploadFiles(e, type) {
        let formData = new FormData();
        let files = e.target.files;

        formData.append('type', type);
        formData.append('room_uuid', room_uuid);

        for (let f of files) {
            formData.append('file', f, f.name);
        }

        for (let en of formData.entries()){
            console.log(en)
        }

        fetch('./audio/upload', {
            method: 'POST',
            body: formData
        }).then((response) => response.json()).then((result) => {
            console.log(result);
            if (result.success == true) {
                getFilenames(type);
            }
        })
    }
    function fileSelectorSelect(filename, type) {
        let new_track = {
                'name': filename,
                'volume': 0.5
        };
        if (type === 'music'){
            current_ambience.music.tracks.push(new_track);
        }
        else if (type === 'sfx'){
            let curr_tracks = current_ambience.sfx.layers[active_sfx_layer_idx].tracks;
            let new_chance = 1 / (curr_tracks.length + 1);
            new_track.chance = recalcChances(new_chance);
            current_ambience.sfx.layers[active_sfx_layer_idx].tracks.push(new_track);
        }
        // trigger svelte reactivity
        current_ambience = current_ambience;

        writeAmbienceJson(`add_track.${type}.${active_sfx_layer_idx}`,
            new_track);
    }
</script>

<Modal bind:isOpen={fileselectorOpen}>
    <div slot='header'>
        {#if fileSelectorType === 'music'}
            <h3>Choose a Music Track</h3>
        {/if}
        {#if fileSelectorType === 'sfx'}
            <h3>Choose an Sfx Track</h3>
        {/if}
    </div>
    <div slot='content'>
        <ul>
            {#if fileSelectorType === 'music'}
                {#each filenamesMusic as filename}
                    <div class='fileselector-item'
                         on:click={() => {fileSelectorSelect(filename, 'music')}}
                         >
                        {filename}
                    </div>
                {/each}
            {/if}
            {#if fileSelectorType === 'sfx'}
                {#each filenamesSfx as filename}
                    <div class='fileselector-item'
                         on:click={() => {fileSelectorSelect(filename, 'sfx')}}
                         >
                        {filename}
                    </div>
                {/each}
            {/if}
        </ul>
    </div>
    <div slot='footer'>
        <h3>Upload File</h3>
        (Maximum 10MB)
        {#if fileSelectorType === 'music'}
        <input type="file"
               accept='.ogg, .mp3, .wav'
               on:change={(e) => {uploadFiles(e, 'music')}}
               >
        {/if}
        {#if fileSelectorType === 'sfx'}
        <input type="file"
               accept='.ogg, .mp3, .wav'
               on:change={(e) => {uploadFiles(e, 'sfx')}}
               >
        {/if}

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
                                    <button on:click={() => {rm_music_track(index)}}>
                                        X
                                    </button>
                                </div>
                            {/each}
                            <div class='track-list-item'>
                                <button on:click={() => {chooseFile('music')}}>
                                    +
                                </button>
                                Insert new track.
                            </div>
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
                                     chanceSliderValues = [];
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
                                        writeAmbienceJson(`sfx.layers.${index}.volume`, e.detail.value, false);
                                        }
                                        }}
                                        on:stop={(e) => {
                                        sliding = false;
                                        writeAmbienceJson(`sfx.layers.${index}.volume`, e.detail.value);
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
                                        writeAmbienceJson(`sfx.layers.${index}.interval`, e.detail.values, false);
                                        }
                                        }}
                                        on:stop={(e) => {
                                        sliding = false;
                                        writeAmbienceJson(`sfx.layers.${index}.interval`, e.detail.values);
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
                                        writeAmbienceJson(`sfx.layers.${active_sfx_layer_idx}.tracks.${index}.volume`, e.detail.value, false);
                                        }
                                        }}
                                        on:stop={(e) => {
                                        sliding = false;
                                        writeAmbienceJson(`sfx.layers.${active_sfx_layer_idx}.tracks.${index}.volume`, e.detail.value);
                                        }}
                                        />
                                </div>
                                <div class="track-list-item-slider">
                                    <div>
                                        C
                                    </div>
                                    <RangeSlider
                                        id="chance-slider"
                                        bind:values={chanceSliderValues[index]}
                                        min={0.05} max={0.95} float step={0.05}
                                        springValues={{stiffness:0.3, damping:1}}
                                        on:start={() => {
                                        sliding = true;
                                        }}
                                        on:change={(e) => {
                                        currentSlidingIndex = index;
                                        track.chance = recalcChances(e.detail.value, index);
                                        if(is_active){
                                        writeAmbienceJson(`sfx.layers.${active_sfx_layer_idx}.tracks.${index}.chance`, e.detail.value, false);
                                        }
                                        }}
                                        on:stop={(e) => {
                                        sliding = false;
                                        currentSlidingIndex = -1;
                                        writeAmbienceJson(`sfx.layers.${active_sfx_layer_idx}.tracks.${index}.chance`, e.detail.value);
                                        }}
                                        />
                                </div>
                                <button on:click={() => {
                                        rm_sfx_track(index, active_sfx_layer_idx)
                                        }}>
                                    X
                                </button>
                            </div>
                        {/each}
                        <div class='track-list-item'>
                            <button on:click={() => {chooseFile('sfx')}}>
                                +
                            </button>
                            Insert new track.
                        </div>
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

    .fileselector-item {
        text-align: center;
        display: flex;
        padding: 0.5em 1em;
        border-style: outset;
        border-color: #EB8034;
        border-radius: 4px;
        margin: 0.5em;
    }
</style>
