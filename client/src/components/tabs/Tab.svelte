<script>
	import { getContext } from 'svelte';
	import { TABS } from './Tabs.svelte';

	const tab = {};
	const { registerTab, selectTab, selectedTab } = getContext(TABS);

	registerTab(tab);
</script>

<style>
      button {
            background: none;
            border: none;
            border-bottom: 2px solid #EB8034;
            border-radius: 0;
            margin: 0;
      }

      .selected {
            background: color;
            background-color: #EB8034;
            border-bottom: 2px solid #EB8034;
      }
</style>

<button class:selected="{$selectedTab === tab}" on:click="{() => selectTab(tab)}">
	<slot></slot>
</button>
