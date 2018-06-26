<template>
    <div>
        <md-card class="main-card">
            <md-card-header class="main-card-header fix-padding">
                <md-card-header-text>
                    <h3 class="md-title card-title">Clusters</h3>
                </md-card-header-text>
                <md-button @click="reload()" md-theme="default" class="md-icon-button md-fab-top-right md-primary">
                    <md-icon>replay</md-icon>
                </md-button>

            </md-card-header>

            <md-table-card class="clean-card">
                <md-table>
                    <md-table-header>
                        <md-table-row>
                            <md-table-head>Name</md-table-head>
                            <md-table-head># Nodes</md-table-head>
                            <md-table-head># Jobs</md-table-head>
                            <md-table-head>Memory Usage</md-table-head>
                            <md-table-head>CPU Usage</md-table-head>
                            <md-table-head>Labels</md-table-head>
                            <md-table-head>Active</md-table-head>
                            <md-table-head>Enabled</md-table-head>
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
                                {{ c.jobs.queued }} / {{ c.jobs.scheduled }} / {{ c.jobs.running }}
                            </md-table-cell>
                            <md-table-cell>
                                {{ (c.memory.running/1024).toFixed(1) }}GB
                                of {{ (c.memory_capacity / 1024 / 1024).toFixed(1) }}GB
                            </md-table-cell>
                            <md-table-cell>
                                {{ c.cpu.running }} of {{ c.cpu_capacity }}
                            </md-table-cell>
                            <md-table-cell>
                                {{ c.labels }}
                            </md-table-cell>
                            <md-table-cell>
                                {{ c.active }}
                            </md-table-cell>
                            <md-table-cell>
                                {{ c.enabled }}
                            </md-table-cell>
                        </md-table-row>
                    </md-table-body>
                </md-table>
            </md-table-card>
        </md-card>
    </div>
</template>

<script>
import store from '../../store'
import AdminService from '../../services/AdminService'

export default {
    name: 'AdminClusers',
    store,
    created () {
        AdminService.loadClusters()
    },
    methods: {
        reload () {
            AdminService.loadClusters()
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

