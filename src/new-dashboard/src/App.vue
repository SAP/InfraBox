<template>
  <div id='app'>
    <ib-notifications></ib-notifications>
<md-toolbar>
  <md-button class="md-icon-button">
    <md-icon>menu</md-icon>
  </md-button>

  <h2 class="md-title" style="flex: 1">Default</h2>

  <md-button class="md-icon-button">
    <md-icon>favorite</md-icon>
  </md-button>
</md-toolbar>

	<md-layout md-gutter>
	  <md-layout md-flex-xsmall="100" md-flex-small="50" md-flex-medium="33">
		<md-list>
            <md-subheader>Projects</md-subheader>

			<md-list-item md-expand-multiple v-for="p in $store.state.projects" :key="p.id">
			  <md-icon v-if="p.state === 'running'">autorenew</md-icon>
			  <md-icon v-if="p.state === 'finished'">done</md-icon>
			  <md-icon v-if="p.state === 'failure'">accessible</md-icon>
			  <span>{{ p.name }}</span>

			  <md-list-expand>
				<md-list>
                  <md-list-item class="md-inset">
                    <router-link :to="{
                        name: 'ProjectDetail',
                        params: {
                            projectName: p.name
                        }
                    }">
                        All Builds
                    </router-link>
                  </md-list-item>

				  <md-list-item class="md-inset" v-for="b in p.getActiveBuilds()" :key="b.id">
                    <router-link :to="{
                        name: 'BuildDetail',
                        params: {
                            projectName: p.name,
                            buildRestartCounter: b.restartCounter,
                            buildNumber: b.number
                        }
                    }">
                      {{ b.number }}.{{ b.restartCounter }}
                    </router-link>
                  </md-list-item>
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
    store
}
</script>
