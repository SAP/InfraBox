<template>
  <div id='app'>
	<md-layout md-gutter>
	  <md-layout md-flex-xsmall="100" md-flex-small="50" md-flex-medium="33">
		<md-list>
			<md-list-item md-expand-multiple v-for="p in $store.state.projects" :key="p.id">
			  <md-icon>whatshot</md-icon>
			  <span>{{ p.name }}</span>

			  <md-list-expand>
				<md-list>
				  <md-list-item class="md-inset">World</md-list-item>
				  <md-list-item class="md-inset">Americas</md-list-item>
				  <md-list-item class="md-inset">Europe</md-list-item>
				</md-list>
			  </md-list-expand>
			</md-list-item>

			</md-list-item>
		  </md-list>
	  </md-layout>

	  <md-layout md-flex-xsmall="100" md-flex-small="50" md-flex-medium="33">
		<router-view/>
	  </md-layout>
	</md-layout>
  </div>
</template>

<script>
import store from './store'

export default {
  name: 'app',
  store,
  beforeCreate () {
    this.$store.dispatch('loadProjects')
  }
}
</script>
