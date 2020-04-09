<template>
	<md-card class="main-card">
		<md-card-header class="main-card-header fix-padding">
			<md-card-header-text>
				<h3 class="md-title card-title">
					<md-layout>
						<md-layout md-vertical-align="center">Clusters</md-layout>
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
                  <md-switch v-model="c.enabled" v-on:change="setCluster(c.name, $event)"></md-switch>
						</md-table-cell>
						<md-table-cell>
                            {{ moment(c.last_active) }}
						</md-table-cell>
						<md-table-cell>
                            {{ moment(c.last_update) }}
						</md-table-cell>
					</md-table-row>
				</md-table-body>
			</md-table>

		</md-table-card>
	</md-card>
</template>

<script>
import moment from 'moment'
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
            this.clusters = store.state.admin.clusters
        })
    },
    methods: {
        moment (v) {
            return moment(v).format('MMMM Do, hh:mm:ss')
        },

        setCluster (name, e) {
            const c = this.clusters.find(c => c.name === name)
            AdminService.updateCluster(c.name, e).then(() => {
                console.log(c.name, e)
                NotificationService.$emit('NOTIFICATION', new Notification({ message: `cluster ${c.name} is ${c.enabled ? 'enabled' : 'disabled'}` }))
            }).catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
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

