<script>
    import { getContext } from 'svelte';
    import { TABS } from './Tabs.svelte';

    const tab = {};
    const { registerTab, selectTab, selectedTab } = getContext(TABS);

    registerTab(tab);
</script>

<style>
    button {
        font-family: 'Cantarell';
        font-weight: bold;
        letter-spacing: 0.15em;
        color: white;
        background: #926B48;
        border: none;
        border-radius: 0px;
        border-top-right-radius: 16px;
        border-top-left-radius: 16px;
        margin: 0.2em;
        margin-bottom: 0;
        padding: 0.5em 1em 0.3em 1em;
    }

    .selected {
        font-family: 'Cantarell';
        font-weight: bold;
        letter-spacing: 0.15em;
        color: #CA9064;
        background: #ECDCB1;
        box-shadow: 12px -4px 10px -7px rgba(0,0,0,0.68);
    }
</style>

<button class:selected="{$selectedTab === tab}" on:click="{() => selectTab(tab)}">
    <slot></slot>
</button>
