<template>
  <div id='app'>
    <ib-notifications></ib-notifications>
    <md-toolbar>
      <md-button class="md-icon-button">
        <md-icon>menu</md-icon>
      </md-button>

      <h2 class="md-title" style="flex: 1">InfraBox</h2>

      <md-button class="md-icon-button">
        <md-icon>favorite</md-icon>
      </md-button>
    </md-toolbar>
	<router-view/>
  </div>
</template>

<script>
import store from './store'

export default {
    name: 'app',
    store
}
</script>
