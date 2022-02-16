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
        recalcChances(0, track_index);
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
    // changes, or is inserted as a new one, by not setting 'track_idx' (ergo,
    // changes from 0->x).
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
            console.log(new_perc * old_percentage);
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

<Modal
    bind:isOpen={fileselectorOpen}>
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
                <div class="music-grid-container tab-panel">
                    <div class="grid-item" id="music-panel-settings">
                        <div id='music-volume'>
                            <label class="settings-label" style='margin-top: 0;' for="g-mus-vol">
                                Music Volume
                                <img src="data:image/png;base64,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1z0CfL2L8Sz/c3+OHjVnMSAgEs8yw7SJN4inNm2D8z5xhBVllficeNSkCxI/cl3x+I1zwWWBZ0bMdGqeOEIsFtpYaWNWNDXiSeKoqumUL2Q8VjlvcdbKVda8J39hOKevLHOd5hASWMQSJIhQUEUJZdiI0aqTYiFF+3Ef/6Drl8ilkKsERo4FVKBBdv3gf/C7Wys/Me4lheNA54vjfAwDoV2gUXOc72PHaZwAwWfgSm/5K3Vg+pP0WkuLHgG928DFdUtT9oDLHWDgyZBN2ZWCNIV8Hng/o2/KAv23QPea11tzH6cPQJq6St4AB4fASIGy133e3dXe279nmv39AGOrcqHMalvDAAANGmlUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz4KPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iWE1QIENvcmUgNC40LjAtRXhpdjIiPgogPHJkZjpSREYgeG1sbnM6cmRmPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJkZi1zeW50YXgtbnMjIj4KICA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIgogICAgeG1sbnM6eG1wTU09Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9tbS8iCiAgICB4bWxuczpzdEV2dD0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL3NUeXBlL1Jlc291cmNlRXZlbnQjIgogICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICAgeG1sbnM6R0lNUD0iaHR0cDovL3d3dy5naW1wLm9yZy94bXAvIgogICAgeG1sbnM6dGlmZj0iaHR0cDovL25zLmFkb2JlLmNvbS90aWZmLzEuMC8iCiAgICB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iCiAgIHhtcE1NOkRvY3VtZW50SUQ9ImdpbXA6ZG9jaWQ6Z2ltcDpmMjc1M2QyOS00ODMzLTQ0ZDYtOGQ0MS1jZDY2YTkyOTAyODQiCiAgIHhtcE1NOkluc3RhbmNlSUQ9InhtcC5paWQ6NmU0NDRkZjgtNzhjOC00YTgzLThhOTYtZDAxMDViOTM0ZTU1IgogICB4bXBNTTpPcmlnaW5hbERvY3VtZW50SUQ9InhtcC5kaWQ6ZjNiNzNjNDctYjk4NS00OTY1LWEwNWEtOWVmMTliZDYyNjJkIgogICBkYzpGb3JtYXQ9ImltYWdlL3BuZyIKICAgR0lNUDpBUEk9IjIuMCIKICAgR0lNUDpQbGF0Zm9ybT0iTGludXgiCiAgIEdJTVA6VGltZVN0YW1wPSIxNjQ0OTgxOTQ0ODgwMzI2IgogICBHSU1QOlZlcnNpb249IjIuMTAuMzAiCiAgIHRpZmY6T3JpZW50YXRpb249IjEiCiAgIHhtcDpDcmVhdG9yVG9vbD0iR0lNUCAyLjEwIj4KICAgPHhtcE1NOkhpc3Rvcnk+CiAgICA8cmRmOlNlcT4KICAgICA8cmRmOmxpCiAgICAgIHN0RXZ0OmFjdGlvbj0ic2F2ZWQiCiAgICAgIHN0RXZ0OmNoYW5nZWQ9Ii8iCiAgICAgIHN0RXZ0Omluc3RhbmNlSUQ9InhtcC5paWQ6OTIxMjU0ZWQtMjYzYi00YTFkLTk4ZDgtM2UzZjQ4ZjBjNTYwIgogICAgICBzdEV2dDpzb2Z0d2FyZUFnZW50PSJHaW1wIDIuMTAgKExpbnV4KSIKICAgICAgc3RFdnQ6d2hlbj0iMjAyMi0wMi0xNlQwNDoyNTo0NCswMTowMCIvPgogICAgPC9yZGY6U2VxPgogICA8L3htcE1NOkhpc3Rvcnk+CiAgPC9yZGY6RGVzY3JpcHRpb24+CiA8L3JkZjpSREY+CjwveDp4bXBtZXRhPgogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAg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" alt='volume icon'>
                                <RangeSlider
                                    pips all='label'
                                    id='g-mus-vol'
                                    slider
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
                        </div>
                        <label class="settings-label">Shuffle
                            <img src=" data:image/png;base64,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SHpyZVN6TlRjemtjOWQiPz4KPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iWE1QIENvcmUgNC40LjAtRXhpdjIiPgogPHJkZjpSREYgeG1sbnM6cmRmPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJkZi1zeW50YXgtbnMjIj4KICA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIgogICAgeG1sbnM6eG1wTU09Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9tbS8iCiAgICB4bWxuczpzdEV2dD0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL3NUeXBlL1Jlc291cmNlRXZlbnQjIgogICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICAgeG1sbnM6R0lNUD0iaHR0cDovL3d3dy5naW1wLm9yZy94bXAvIgogICAgeG1sbnM6dGlmZj0iaHR0cDovL25zLmFkb2JlLmNvbS90aWZmLzEuMC8iCiAgICB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iCiAgIHhtcE1NOkRvY3VtZW50SUQ9ImdpbXA6ZG9jaWQ6Z2ltcDplOGM3ZjczNi03OTc3LTRlOTctOWY3Yi0wMjIxNWM1NTFjNmQiCiAgIHhtcE1NOkluc3RhbmNlSUQ9InhtcC5paWQ6NjM1YmUwMzktY2Y2NC00YzZhLWFlNDEtOGYzYzJmOTUwZDZlIgogICB4bXBNTTpPcmlnaW5hbERvY3VtZW50SUQ9InhtcC5kaWQ6MzM0MjlkMzAtNTdjYS00MjZlLTg4YzUtMTNiZTY2NjdhNGVjIgogICBkYzpGb3JtYXQ9ImltYWdlL3BuZyIKICAgR0lNUDpBUEk9IjIuMCIKICAgR0lNUDpQbGF0Zm9ybT0iTGludXgiCiAgIEdJTVA6VGltZVN0YW1wPSIxNjQ0OTg1MTE0MjAzMTU4IgogICBHSU1QOlZlcnNpb249IjIuMTAuMzAiCiAgIHRpZmY6T3JpZW50YXRpb249IjEiCiAgIHhtcDpDcmVhdG9yVG9vbD0iR0lNUCAyLjEwIj4KICAgPHhtcE1NOkhpc3Rvcnk+CiAgICA8cmRmOlNlcT4KICAgICA8cmRmOmxpCiAgICAgIHN0RXZ0OmFjdGlvbj0ic2F2ZWQiCiAgICAgIHN0RXZ0OmNoYW5nZWQ9Ii8iCiAgICAgIHN0RXZ0Omluc3RhbmNlSUQ9InhtcC5paWQ6NGFkODkwMmUtNjBjNS00MGYzLTk5MmMtYjg1YjM1NzQyM2ZmIgogICAgICBzdEV2dDpzb2Z0d2FyZUFnZW50PSJHaW1wIDIuMTAgKExpbnV4KSIKICAgICAgc3RFdnQ6d2hlbj0iMjAyMi0wMi0xNlQwNToxODozNCswMTowMCIvPgogICAgPC9yZGY6U2VxPgogICA8L3htcE1NOkhpc3Rvcnk+CiAgPC9yZGY6RGVzY3JpcHRpb24+CiA8L3JkZjpSREY+CjwveDp4bXBtZXRhPgogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgCjw/eHBhY2tldCBlbmQ9InciPz5YlcldAAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAAOxAAADsQH1g+1JAAAAB3RJTUUH5gIQBBIijI3PKwAADLpJREFUeNrtnXmQVcUVxn8zA7IMgoBxiVhuEdcIibgU2a4KWqhARAUbY6KoGEUhGKOibWn0YikEBVOiomiiyMWoUVFxDbagJlBoBgSjMbiBCohGdIZFZCZ/dL/K8zrLW26/d++7/VW9mqo393b36/P16e7T55wGBwcHBwcHBwcHBwcHBwcHBwcHh8pHleuC+CHwve5AV2CVkKrRESAdQq8BLgQuAvYxX9cDDwFSSPWhI0DlCr8z8CgwsIVH6oFzhFQPRF13tev+WOCmVoQP0AWYE/jeHYHvbec0QGWN/t2B9/OQxRLgVCHVe04DVAaG5DkQ+wGLA98b4AhQGehewDvfAZ4NfO+GwPeqHQGSja1FTN+XAXMD3+vhCJBcvFvk+ycAdYHvHeEIkEy8HUEZuwMvBr43zu0CkrcLqAW+jFAWs4DzhFQbcyZA4Hv9gQNz0AibgQZgg2l0vfl8JKTa6sTZprB3BnYBepq+3sHI4B6gNsKqlgKnCKn+0yYBAt+bCFwRwULmXeBN4N/AW8A/gToh1baUCbkTcBDQF+gDHGxUdC+gQwmbsgE4U0j1aFsE2IA+eLCBz4EFwHzgBeB1IVVThQl8O+BI4BhgAHA40C4mzWsCJgNXCqm+bokApRTIamA2cJ+QannChX4ccBrakNMl5k1+EThNSLWm3ATIRh1wHzBLSLUuIYLvA4wBTqEwA0458TEwQki1MC4EyGATMBOYLKT6IIZCrwGGoo9pvYTPWF8DlwM3ZabiOBAgeyE5C7hRSPVWDARfBZwK/B7Yv8LWqg8BZwipNseJABk0AncBE4RUn5VJ+IOA681KvlLxBDAkjgTIYL1RV/fYdovKEvzuwC3Az1Oyaz09zgTI4B/A+UKqOsvz/Fjg2gSs6KPE/CQQILN4kcCkqO0IZtTfB/yM9OGzpBwGtQNuAB42HrNRCX+Y2Y6mUfgA7ZN2GngS8Frge4cXKfjqwPcmAQ8DPUgv3kzicfCewILA904uUPhdgL8Cv8NhdlL9AToADwS+d16ewt8VWIg27KQdS4HpSXYIqQFuD3xP5ij8XoCq8L19PsI/Tkj1VSV4BF1n5vPWhL8H+kCkt5M99wL9hVRrIV6m4GJxkJDqjRbU/itm7ZBmbAHGCanuCG+vKgWdmxF+V2CeEz7voz2EloT/UY127Uo6FgKvhoTfHn3okfY5/yng0OaEnyHAnQn/gV+iXZ/CU9k0Wo+3q3Q0AlcDJwqpPm3poYxT6ABg7xwLrgW6ZX32RPu+lcugMkpIdU9o9J9hFjtxwVfAG8B7wAfAOrR5+3O029Yk05dRYT1wupDq2bYejMwt3NjU+6BdpQYDe5SgYx8RUg0LteP76AOkzmVecM0HnkP7Qq5oyWs68L0OwEaii9FYhA4eXZXLw5EtAk2Fq9DnzBcFvtcXGAGMtqQdPjVlhztzThmF/yJwN/CYkGpDju/sE6HwbwUuFlJ9lesL1nYB5vi2LvC964BfAr8B9ouwiquFVOvD36HjG0o91wbok8plBby/bwRtaABGC6lm5/ui9W2giVC5PfC9O82IvQ4dGFEMlgN3hEZ/P0pv338SuLQ5+0Me2KfINrxptngrCnm5ZHYAEyByW+B7DwA+cF4Rqm98tp+7cei4s4S/50PgwraCLgq1X+SBB4GzhVQFb+VLbggyfn4XBL43F+2IsWOeRTwrpHo+9N1ZJdzvPwj8OkJ/xU0FvLPVaJ6pxVZetrMAIdXTwA+Al/N81Q+p/u3Rrly2sQ24XEg1PGJn1WcK0D5HRSH8shLAkGA1cBTwl1xX2eHABnSShF0tN7XBGFRutNAHy9HWulzwAtqq93JU9Zf9NNDsj0cCfy5g9O+ADtiwic+BY43GsoWz0EG1LaEJ7RI3MHOKVzEEyFogjqJ1s/SyZub+C7AX2Iox0BwvpHrF8u9fiw4qvauZNcESo/In2Ii0jlWCiMD32qFP75qz4X/D5GuSK74L7GRxzh8qpHqyxH3QHR1e3h1tQXzHZn2xyxBiOmBRyECyDthDSLU567nzgekWm3KpkGoyFY7YeQQJqf6L9tnLXmlfGxJ+leW5/xHgD6QAsXQJE1L9y2wRz0a7L90aeuRY4ABL1a9D59hpSgMBEpkkKvC9ecAgS8WfZiMps9MA0Qm/N/rI2QZezsMm4QhQJoyz1O4mYGxaVH8ipwBj+FmFnQjeJ4RUg0kZkqYBzsFe+PYNpBBVCRr9Nei0qntZKH6JkOqwNBIgSRrgJEvCB31jB44A8V/82cBH6DBxR4AYq/8fAj+2VPz0fJwoHQHKg/GWyt0MzCDFqE7A6N8bnZLVBu4XUn3iCBBvXIk938VbSDmqYj76+6IdImosFD9fSHVM2glQHWPhV6EDPGvc6LeHOOcHGAP81FLZ76BD2LIJ1w0Yho42fiwtN6BUxXT0729Uf62lKsZnu1Wb/P91/N/H4CFgeBoOhqpjKPwuaMOMLeF/ib6jJxsj+KaDySnANW4KKL3wa4D7sRvgOaOZyN0Lm3nuqsD3lgupHixxH/Q0v78nOgZypU1NVBUj4Veh3aJHWaxmM7C3kOrjrHoPRzuhNocGYFAzwSg2fn83tB/iL4COWf9aAvxWSLWgYqcAc//tbZaFD3B3tvANWosorgWeDnxvoOXfvwuwGH3c3TH0736ACnxvotGQlUUAk9ThXnS0sE1sQadiCS82h7XxXmf0/bwnWmzbTFrPYViFvtrvmcD3dqoYAgS+tyPwNHB6CaqbKqR6P/Td5Tn2QUfg0cD3rin2tu5m+uBg4PgcHz8GnSy7f+IJYBJTLaU0FzGtRV8Bk13/99AxibmiBp2B5AlD3KiQr4PrbmZKGJtIAgS+1zXwvWnosOjvlqhaKaT6IvTdZKB9AWUNQqe+ieqAqlMB77QHpgW+N8dsm+NPgMD3agLfOxOd0mRsCeteiE7clN2WoynuXqDdgCDwPRX43iFFtm9TEe+OABYHvlfwtrmqBILvAAxHn+rtV2KF0wD0EVKtDNkaXgMOiaiObej7B6YWEkUc+N5QoNhUM/XAuUKqObEhgFncjDRbu53LtNQYI6SaHmrXWPQhkw0sAm4HHm8tO2eoPQcCKyKq/4/AJfl4OEWZKLIn+hLlo83C5qAy7zDnobN6NGW1cT8z+m3nEdwGvATMNX9XCKkaWui3jkZTRTUl/h19jrE6ZwLkmSq2Pdo3vxZ9JXovtB29F/HBO0A/E2mc6eh2RhhHlKE9jcBKtGl3HTrrSObTaBakUSa6+AQY2UxCjW8TIPC9KcDFVA42oiOKl4ZG2lWUJplUXLANfaA1sbWzhGrg3Ar60Y3oTCJh4fcFriJdqEEn5Xw88L0erRFg+wr60eNbCO0eV+CevxJwArAk8L1DY2EIsoiJQqpbWpkW0oy9gJcC3zu3Uglws5CqtdvDJpqFYZrREZgR+N6fAt/rVEkE8IVUrS5ihVQfoSOLluPwK+CVwPd2zuwCkur31oRO3TopD1tFD3SG7yMdD1gGHJZUDbDJ7HMn5fOSyfE70JAg7TgEGJNEAqwGflKI3duQoB4YYmwCTSknwcikTQHPA2cIqdZEUVjge0PQ3kjdUkqA+qRogC3AJej7btdEVaiQai5wKPrIOI3YmgQC1AFHCqmmCKkaoy7cHBV76BD0tNkL6uJMgA1ox5F+5gIqaxBSNZpIob5oH8W0YGYc1wBfo6+SuSJKdZ/n2mAQMAV76WjjgCeBwXHSAI3AbPQt4KPKJXyjEZ4y26TR6GPcSsPD6JvGmuKgATYZwd9c6NVnlrVBDdr37jKicyMrp3adAEzJHBGXkwAr0Xf/zYz4EiabZPgR+vh8OIV585YTH6MTYX8jxKzUBPgQnYx5jpBqcVKHkUlZOxQ4GZ26vkPMm7zACD8cFkdV4HsbsHfvzkZ0Bu6/mc9rNrZyZSZDV7Qf5AB05M7+MWpek1nMTsi+aDNMgOvNvFDs3LLGqPXXzd69Dng9bTn4TJRvn9CnN3Yvt2ppG32WkOqR1h7KOIX2R3vxtuUlvBXtg74JHWr9Bdo2v9bGjVYVRoxO6EioXdBu8plI347oyOgoE2IsM6v8t9t6sMqJpuzEqEVnLYlKFrPQV9s25PJwOyeCsmPfiIS/BbhMSJVX0IsjQPnRO4IyVgGnCqkW5ftitev/sqPYFPjzgL6FCN8RIB4o1F29CbgRGFyMIc1NAeVHIcJbj3aJe67Yyp0GKD/mkp9r2qvAYVEI3xEgBjBRvLneWTADHff4XlT1uykgHrgY2JOW8wXVA6OFVEHUFTsNEA8tsBEdw3cR8FbWvzJpbQ+wIXxwlsBYwiR+6gGsSttNpg4ODg4ODg4ODg4ODg4ODg4ODg428D8ipC3qIacR4AAAAABJRU5ErkJggg==" alt='shuffle icon'>
                            <br>
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
                            <img src=" data:image/png;base64,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Ej9yXfH4jXPBZYFnRsx0ap44QiwW2lhpY1Y0NeJJ4qiq6ZQvZDxWOW9x1spV1rwnf2E4p68sc53mEBJYxBIkiFBQRQll2IjRqpNiIUX7cR//oOuXyKWQqwRGjgVUoEF2/eB/8LtbKz8x7iWF40Dni+N8DAOhXaBRc5zvY8dpnADBZ+BKb/krdWD6k/RaS4seAb3bwMV1S1P2gMsdYODJkE3ZlYI0hXweeD+jb8oC/bdA95rXW3Mfpw9AmrpK3gAHh8BIgbLXfd7d1d7bv2ea/f0AY6tyocxqW8MAAA0aaVRYdFhNTDpjb20uYWRvYmUueG1wAAAAAAA8P3hwYWNrZXQgYmVnaW49Iu+7vyIgaWQ9Ilc1TTBNcENlaGlIenJlU3pOVGN6a2M5ZCI/Pgo8eDp4bXBtZXRhIHhtbG5zOng9ImFkb2JlOm5zOm1ldGEvIiB4OnhtcHRrPSJYTVAgQ29yZSA0LjQuMC1FeGl2MiI+CiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPgogIDxyZGY6RGVzY3JpcHRpb24gcmRmOmFib3V0PSIiCiAgICB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIKICAgIHhtbG5zOnN0RXZ0PSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvc1R5cGUvUmVzb3VyY2VFdmVudCMiCiAgICB4bWxuczpkYz0iaHR0cDovL3B1cmwub3JnL2RjL2VsZW1lbnRzLzEuMS8iCiAgICB4bWxuczpHSU1QPSJodHRwOi8vd3d3LmdpbXAub3JnL3htcC8iCiAgICB4bWxuczp0aWZmPSJodHRwOi8vbnMuYWRvYmUuY29tL3RpZmYvMS4wLyIKICAgIHhtbG5zOnhtcD0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wLyIKICAgeG1wTU06RG9jdW1lbnRJRD0iZ2ltcDpkb2NpZDpnaW1wOmM2ODQwODlmLWZkMDItNDBjYy04OTA0LTE1ZjYzOWRjMzE5OSIKICAgeG1wTU06SW5zdGFuY2VJRD0ieG1wLmlpZDphYjQyOGU4Ni0yZTcxLTQwYmEtYjMxZS1iODMyOWYwNzNhNDMiCiAgIHhtcE1NOk9yaWdpbmFsRG9jdW1lbnRJRD0ieG1wLmRpZDo5ODk2NzU3MS1mMDNmLTRjY2YtYTE2My04YWRlYzM4ZDU4YmYiCiAgIGRjOkZvcm1hdD0iaW1hZ2UvcG5nIgogICBHSU1QOkFQST0iMi4wIgogICBHSU1QOlBsYXRmb3JtPSJMaW51eCIKICAgR0lNUDpUaW1lU3RhbXA9IjE2NDQ5ODUzMjI2NTkwNzAiCiAgIEdJTVA6VmVyc2lvbj0iMi4xMC4zMCIKICAgdGlmZjpPcmllbnRhdGlvbj0iMSIKICAgeG1wOkNyZWF0b3JUb29sPSJHSU1QIDIuMTAiPgogICA8eG1wTU06SGlzdG9yeT4KICAgIDxyZGY6U2VxPgogICAgIDxyZGY6bGkKICAgICAgc3RFdnQ6YWN0aW9uPSJzYXZlZCIKICAgICAgc3RFdnQ6Y2hhbmdlZD0iLyIKICAgICAgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDo4NmU2ZGRjYi1mNDEwLTQyZDQtYWI4Zi05NDhlM2Y5MjY2YWQiCiAgICAgIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkdpbXAgMi4xMCAoTGludXgpIgogICAgICBzdEV2dDp3aGVuPSIyMDIyLTAyLTE2VDA1OjIyOjAyKzAxOjAwIi8+CiAgICA8L3JkZjpTZXE+CiAgIDwveG1wTU06SGlzdG9yeT4KICA8L3JkZjpEZXNjcmlwdGlvbj4KIDwvcmRmOlJERj4KPC94OnhtcG1ldGE+CiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAKPD94cGFja2V0IGVuZD0idyI/PgSd3fsAAAAGYktHRAD/AP8A/6C9p5MAAAAJcEhZcwAAA3YAAAN2AX3VgswAAAAHdElNRQfmAhAEFgLTjyrnAAACiUlEQVR42u3doW4UURiG4Q9CuikCLgBDgmuRSEjGoXoBQ4IsEhCQIEaOQCAAW0lgLgCFG9GEGyh1JJg6TBGQRTSI7iYEA6bz093nUev+0553d2cnJ5kEAAAAAABYZReWL4a+mSXZTnLljGeeJPncduORf/9/EsDQNw+TPE+yOeHs/ST32278YhsKAxj65l6St0XzD5LcartxbitqXEzypHD+zSR3bUNtANvFa9i2DbUBbBSvYWYbagNAAAgAAbB+Lq3KHzL0zdUkWxNcVM6THLbdeCyA/2PjLyd5mWR34rl7SR633fhdALUm3/yF5cwHrgFqP/Z3C5ewu1iDAIpsWcN6BzCzBj8DEQACQACs532AlTD0zbUkNyZ4U35L8ml5CksA9Rt/PcmbJLcnHPtj6JtnbTe+FkDt5s+SvM/p0bgpbSZ5NfTNV9cAte4WbP7vngigVvl5TAHUqr6LuCEA9wEQAAJAAAgAASAABIAAEAACQAAIAAEgAASAABAAAkAACAABIAAEgAAQAAJAAAgAASAABIAAEAACQAAIAAEgAASAABAAAkAACAABIAAEgAAQAAJAAAhg5c2L5/8UQK1P1fMFUOtDkoPC+S8EUGjxBO+dJPsTj/6R5FHbje88PLo+gi9J7nh8vBCOkhz5FYAAEAACQAB/N7eG9Q7g0BrWOIC2G4+T7BUuYW+xBgEUelwUwd5i9rl27m8Etd34PcmDoW+eJtlKMpvgO//wvL/zVyaAP74OPrqu9zMQASAABMC/BfCzeA1z21AbQPm5NNtQG8CLwvkHOT0XR1UAbTe+S/Iop+fEprSfZGd5NIkaF5Yvhr6ZJdlOcuWMZ54k+bw4AgUAAAAAAMAZ+gW4OoAE63DCngAAAABJRU5ErkJggg==" alt='crossfade icon'>
                            <br>
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
                                       <br>
                                       <input type="number"
                                              class='crossfade-shuffle-input'
                                              value={current_ambience.music.crossfade.by_secs}
                                              on:change={(e) => {
                                              current_ambience.music.crossfade.by_secs = e.target.value;
                                              writeAmbienceJson('music.crossfade.by_secs', parseFloat(e.target.value));
                                              }}
                                              />
                                   {/if}
                        </label>
                        <label class="settings-label">Pause
                            <img src=" data:image/png;base64,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bXAub3JnL3htcC8iCiAgICB4bWxuczp0aWZmPSJodHRwOi8vbnMuYWRvYmUuY29tL3RpZmYvMS4wLyIKICAgIHhtbG5zOnhtcD0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wLyIKICAgeG1wTU06RG9jdW1lbnRJRD0iZ2ltcDpkb2NpZDpnaW1wOmM1YzdmMDA0LWQ5N2UtNDgyYy1hZjkyLTViMjY1N2NkNDA1NCIKICAgeG1wTU06SW5zdGFuY2VJRD0ieG1wLmlpZDpkYThlOWFkNC1hMDk5LTRlOTQtYWQ0ZS1kMWVmOWY2NmJmOGUiCiAgIHhtcE1NOk9yaWdpbmFsRG9jdW1lbnRJRD0ieG1wLmRpZDpiNDc0MzQxMS03ZDdjLTQ4NTAtYjdlMi00NjVjNDQyMDcyMDEiCiAgIGRjOkZvcm1hdD0iaW1hZ2UvcG5nIgogICBHSU1QOkFQST0iMi4wIgogICBHSU1QOlBsYXRmb3JtPSJMaW51eCIKICAgR0lNUDpUaW1lU3RhbXA9IjE2NDQ5ODUxMDg4OTA4ODIiCiAgIEdJTVA6VmVyc2lvbj0iMi4xMC4zMCIKICAgdGlmZjpPcmllbnRhdGlvbj0iMSIKICAgeG1wOkNyZWF0b3JUb29sPSJHSU1QIDIuMTAiPgogICA8eG1wTU06SGlzdG9yeT4KICAgIDxyZGY6U2VxPgogICAgIDxyZGY6bGkKICAgICAgc3RFdnQ6YWN0aW9uPSJzYXZlZCIKICAgICAgc3RFdnQ6Y2hhbmdlZD0iLyIKICAgICAgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDoxMjk2ZTcyMi0wMjNjLTQzNDMtYjA2My04ZjI4Yjc5MGI2ZTMiCiAgICAgIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkdpbXAgMi4xMCAoTGludXgpIgogICAgICBzdEV2dDp3aGVuPSIyMDIyLTAyLTE2VDA1OjE4OjI4KzAxOjAwIi8+CiAgICA8L3JkZjpTZXE+CiAgIDwveG1wTU06SGlzdG9yeT4KICA8L3JkZjpEZXNjcmlwdGlvbj4KIDwvcmRmOlJERj4KPC94OnhtcG1ldGE+CiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAKPD94cGFja2V0IGVuZD0idyI/PmR1QYAAAAAGYktHRAD/AP8A/6C9p5MAAAAJcEhZcwAAA7EAAAOxAfWD7UkAAAAHdElNRQfmAhAEEhxN7NKAAAACoElEQVR42u3YMWsTYRjA8f/F0XQXGkqlDv0YWbVg6iSH3dxVHJxelEo+gbsgVMhUpGmK630Lt1BojHtbNxtc4lJwaE2ee3P+f3Oa8Dz3vzeXgiRJkiRJ+l8UdX74oN/dAHrADrAJdIC71172E5gAp8AIOCpTdZbjMldxnqKmRa0Db4HnwJ0b/vkMOATelKk6zeTCr+w8RQ3L2gUOgPY/vtUFsFemaljzxV/peVrBy3o5r729gLdbA74M+t0XNV78lZ+nCL5TDpcQ3Qx4En3nNGWeImhZHeDbgu6Uvx2f22Wqps6T51fA+yUu68/xuR94ADRmniLgbtkAxrd4Or6pK2CzTNXEefI6AXYDlsX8M3rOk18ADwOP5kfOk18ADwIXtuU8+QVwL3Bh686TXwDtwIW1nSfPn4HKlAEYgAxABiADkAHIAGQAMgAZgAxABiADkAHIAGQAMgAZgAxABiADkAHIAGQAMgAZgAxABiADkAHIAGQAMgAZgAxABiADkAHIAGQAMgAZgAxABiADkAHIAGQAMgAZgAxABiADkAHIAGQAMgAZgAxABiADkAHIAGQAMgAZgAxABiADkAHIAGQAMgAZgAxABiADkAHIAGQAMgAZgAxABiADkAEoIoDLwHnOnSe/AKaBC5s6T34BjAMXNnae/AI4CVzYyHnyC+AIuAr4nF/AsfNkFkCZqjPgU8DCPpapmjhPnj8D3wEXS35a3g88mhszT0gAZaq+A0+XdHTOgL0yVT+irn6T5mkFLu0r8Ho+4CKX9apM1THBmjJPEb24Qb/7GPgMrC3gmHxWpmpEjVZ9nlYNd84Q2AI+zJ90b3OXHADbdV/8JsxT1Hz3dIAesAPcBzpA+9rLLoHJ/J8iJ8Aw4unYeSRJkiRJUtP8Bg1o08OmAVH6AAAAAElFTkSuQmCC" alt='pause icon'>
                            <br>
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
                                       <br>
                                       <input type="number"
                                              class='crossfade-shuffle-input'
                                              value={current_ambience.music.pause.by_secs}
                                              on:change={(e) => {
                                              current_ambience.music.pause.by_secs = e.target.value;
                                              writeAmbienceJson('music.pause.by_secs', parseFloat(e.target.value));
                                              }}
                                              />
                                   {/if}
                        </label>
                    </div>

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
                                    <button
                                        class='track-button'
                                        on:click={() => {chooseFile('music')}}>
                                        {track.name}
                                    </button>
                                    <div class="track-list-item-slider">
                                        <RangeSlider
                                            pips all='label'
                                            slider
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
                                                    writeAmbienceJson(`music.tracks.${index}.volume`, e.detail.value, false);
                                            }
                                            }}
                                            on:stop={(e) => {
                                                sliding = false;
                                                writeAmbienceJson(`music.tracks.${index}.volume`, e.detail.value);
                                            }}
                                            />
                                    </div>
                                    <button
                                        class='remove-button'
                                        on:click={() => {rm_music_track(index)}}
                                        >
                                        X
                                    </button>
                                </div>
                            {/each}
                            <div class='track-list-item'>
                                <button
                                    class='track-button'
                                    on:click={() => {chooseFile('music')}}>
                                    +
                                </button>
                                Insert new track.
                            </div>
                        </ul>
                    </div>

                </div>
            </TabPanel>
            <TabPanel>
                <div class="sfx-grid-container tab-panel">
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
                                <div class="sfx-layer-list-item-slider slider-selected-label" >
                                    <RangeSlider
                                        pips all='label'
                                        slider
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
                                        pips all='label'
                                        slider
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
                                <button
                                    class='track-button'
                                    on:click={() => {chooseFile('sfx')}}>
                                    {track.name}
                                </button>
                                <div class="track-list-item-slider">
                                    <div>
                                        V
                                    </div>
                                    <RangeSlider
                                        pips all='label'
                                        slider
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
                                <div class="track-list-item-slider general-slider"
                                     class:hidden="{current_ambience.sfx.layers[active_sfx_layer_idx].tracks.length === 1}">
                                    <div>
                                        C
                                    </div>
                                    <RangeSlider
                                        pips all='label'
                                        slider
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
                                <button
                                    class='remove-button'
                                    on:click={() => {
                                    rm_sfx_track(index, active_sfx_layer_idx)
                                    }}
                                    >
                                    X
                                </button>
                            </div>
                        {/each}
                        <div class='track-list-item'>
                            <button
                                class='track-button'
                                on:click={() => {chooseFile('sfx')}}>
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
    /* Main Container */
    .main-container {
        margin: 1em;
    }
    .main-container h2 {
        text-align: center;
        font-family: 'DejaVu Serif';
        font-weight: bold;
        font-variant: small-caps;
        padding: 0.55em;
        background-color: #ECDCB1;
        border-radius: 16px;
        width: fit-content;
        margin: 0 auto;
        color: #593631;
        overflow: hidden;
        position: sticky;
        top: 2px;
        z-index: 50;
    }

    .tab-panel {
        background: #ECDCB1;
        box-shadow: 0 0 20px rgba(0,0,0,0.76);
        border-radius: 16px;
        padding: 1.6em;
        height: 100%;
    }

    /* General Stuffs */
    .hidden {
        display: none;
    }

    ul {
        padding: 0;
    }

    .settings-label {
        font-variant: small-caps;
        color: #A78440;
        font-weight: bold;
        text-align: center;
        margin: 1em auto;
    }
    .settings-label img {
        height: 1em;
        padding: 0.2em;
        margin-bottom: -6px;
    }
    .settings-label input[type="checkbox"]{
        font-size: 1.4em;
        -webkit-appearance: none;
        -moz-appearance: none;
        appearance: none;
        width: 3em;
        height: 1.4em;
        border: solid 2px #926B48;
        border-radius: 3em;
        position: relative;
        cursor: pointer;
        outline: none;
        -webkit-transition: all .2s ease-in-out;
        transition: all .2s ease-in-out;
        margin-bottom: -6px;
        margin-top: 0.5em;
    }

    .settings-label input[type="checkbox"]:checked{
        background: white;
    }

    .settings-label input[type="checkbox"]:after{
        position: absolute;
        left: -2px;
        bottom: -3px;
        content: "";
        text-align: center;
        width: 1.5em;
        height: 1.5em;
        border-radius: 50%;
        background: #CA9064;
        -webkit-box-shadow: 0 0 .25em rgba(0,0,0,.3);
        box-shadow: 0 0 .25em rgba(0,0,0,.3);
        -webkit-transform: scale(.7);
        transform: scale(.7);
        left: 0;
        -webkit-transition: all .2s ease-in-out;
        transition: all .2s ease-in-out;
    }

    .settings-label input[type="checkbox"]:checked:after{
        left: calc(100% - 1.5em);
    }

    /* Music Stuffs */
    .music-grid-container {
        display: grid;
        grid-template-areas:
            'settings'
            'list';
    }
    #music-panel-tracklist {
        grid-area: list;
        overflow: scroll;
        overflow: hidden;
        text-align: center;
    }
    #music-panel-settings {
        text-align: center;
        display: flex;
        grid-area: settings;
        height: 105.2px;
        padding: 0 2em 0 2em;
        border-bottom: solid 2px #926B48;
    }
    #music-volume {
        width: 50%;
        margin: 1em auto;
        padding-bottom: 2em;
    }
    .crossfade-shuffle-input {
        width: 4em;
        height: 2em;
        margin: 0.2em;
        margin-bottom: -2em;
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
        margin: 0 auto;
        border: solid 4px #926B48;
        width: 80%;
        padding: 0.5em 1em;
        border-radius: 16px;
        position: relative;
        display: flex;
        margin: 0.5em auto;
    }
    .track-list-item .track-button {
        background-color: #CA9064;
        border: solid 2px #CA9064;
        border-radius: 16px;
        padding: 0.4em 1.2em 0.4em 1.2em;
        margin: 0.2em;
        margin-right: 2em;
        font-family: 'Open Sans';
        font-weight: bold;
        color: white;
    }
    .track-list-item .track-button:hover {
        background-color: #c48a5e;
        border: solid 2px #a78440;
    }
    .track-list-item .track-button:active {
        color: #ebebeb;
        background-color: #c48a5e;
        box-shadow: inset 0 0 12px rgba(0,0,0,0.5);
    }
    .track-list-item-slider {
        color: black;
        width: 66%;
    }
    .track-list-item .remove-button {
        position: absolute;
        border: solid 3px #926B48;
        border-radius: 100px;
        width: 1.3em;
        height: 1.3em;
        color: #926B48;
        background: none;
        top: 0.4em;
        right: 0.6em;
        font-weight: 900;
        padding: 0px;
        margin: 0px;
        text-align: center;
        line-height: 1px;
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
