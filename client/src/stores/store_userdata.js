import {writable} from 'svelte/store'

// shall contain:
/*  - uid
    - room_uuid
*/
const store_userdata = writable({});

export default store_userdata;
