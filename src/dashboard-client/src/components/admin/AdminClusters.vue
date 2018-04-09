<template>
	<md-card class="main-card">
		<md-card-header class="main-card-header fix-padding">
			<md-card-header-text>
				<h3 class="md-title card-title">
					<md-layout>
						<md-layout md-vertical-align="center">Clusers</md-layout>
					</md-layout>
				</h3>
			</md-card-header-text>
		</md-card-header>

		<md-table-card class="clean-card">
			<md-table>
				<md-table-header>
					<md-table-row>
						<md-table-head>Name</md-table-head>
						<md-table-head># Nodes</md-table-head>
						<md-table-head>Memory Capacity</md-table-head>
						<md-table-head>CPU Capacity</md-table-head>
						<md-table-head>Active</md-table-head>
					</md-table-row>
				</md-table-header>
				<md-table-body>
					<md-table-row v-for="c in $store.state.admin.clusters" :key="c.name">
						<md-table-cell>
                            {{ c.name }}
                        </md-table-cell>
						<md-table-cell>
                            {{ c.nodes }}
						</md-table-cell>
						<md-table-cell>
                            {{ c.memory_capacity }}
						</md-table-cell>
						<md-table-cell>
                            {{ c.cpu_capacity }}
						</md-table-cell>
						<md-table-cell>
                            {{ c.active }}
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

export default {
    name: 'AdminClusers',
    store,
    created () {
        AdminService.loadClusters()
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

