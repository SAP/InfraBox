<template>
	<md-card class="main-card">
		<md-card-header class="main-card-header fix-padding">
			<md-card-header-text>
				<h3 class="md-title card-title">
					<md-layout>
						<md-layout md-vertical-align="center">Projects</md-layout>
					</md-layout>
				</h3>
			</md-card-header-text>
		</md-card-header>

		<md-table-card class="clean-card">
			<md-table>
				<md-table-header>
					<md-table-row>
						<md-table-head>Name</md-table-head>
						<md-table-head>
							Active
						</md-table-head>
						<md-table-head>
							Enabled
						</md-table-head>
						<md-table-head>
							Last Active
						</md-table-head>
						<md-table-head>
              Last Update
						</md-table-head>
					</md-table-row>
				</md-table-header>
				<md-table-body>
					<md-table-row v-for="c in clusters" :key="c.name">
						<md-table-cell>
                            {{ c.name }}
            </md-table-cell>
						<md-table-cell>
                            {{ c.active }}
						</md-table-cell>
						<md-table-cell>
                  <md-switch v-model="c.enabled" v-on:change="setCluster(c.name)"></md-switch>
						</md-table-cell>
						<md-table-cell>
                            {{ c.last_active }}
						</md-table-cell>
						<md-table-cell>
                            {{ c.last_update }}
						</md-table-cell>
					</md-table-row>
				</md-table-body>
			</md-table>

		</md-table-card>
	</md-card>
</template>

<script>
import store from '../../store'
import AdminService from '../../services/AdminService'
import NotificationService from '../../services/NotificationService'
import Notification from '../../models/Notification'

export default {
    name: 'AdminClusters',
    store,
    data: () => {
        return {
            clusters: []
        }
    },
    created () {
        AdminService.loadClusters().then(() => {
            this.clusters = store.state.clusters
        })
    },
    methods: {
        setCluster (name) {
            const c = this.s.find(c => c.name === name)
            AdminService.updateCluster(c.name, c.enabled).then(() => {
              NotificationService.$emit('NOTIFICATION', new Notification({message: `cluster ${c.name} is ${c.enabled ? "enabled": "disabled"}` }))
            })
        }
    }
}
</script>

<style scoped>
.fix-padding {
    padding-top: 7px !important;
    padding-bottom: 22px !important;
    padding-left: 0 !important;
}

</style>

