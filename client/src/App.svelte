<script>
      let socket;

      import FrontPage from './components/FrontPage.svelte';
      import AdminPage from './components/AdminPage.svelte';

      let currentViewport = FrontPage;

      const chviewAdminPage = () => {
            currentViewport = AdminPage;
      };

      const chviewSlavePage = () => { };
</script>

{#if currentViewport == FrontPage}
      <FrontPage createRoomFunc={chviewAdminPage} joinRoomFunc={chviewSlavePage}/>
{:else if currentViewport == AdminPage}
      <AdminPage />
{/if}


<!-- global styling -->
<style>
      :global(body) {
            height: 100%;
            width: 100%;
            padding: 0px;
      }
      :global(p.form_error) {
            font-size: 0.7em;
            margin-top: 0.06em;
            color: red;
      }
      :global(.grid-container) {
            display: grid;
      }
</style>
