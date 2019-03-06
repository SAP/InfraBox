<template>
    <div v-if="joblist">
        <md-table-card class="clean-card add-overflow">
            <md-table class="min-medium" @sort="sort">
                <md-table-header>
                    <md-table-row>
                        <md-table-head md-sort-by="state">State</md-table-head>
                        <md-table-head md-sort-by="name">Job Name</md-table-head>
                        <md-table-head md-sort-by="startDate">Started</md-table-head>
                        <md-table-head md-sort-by="duration">Duration</md-table-head>
                        <md-table-head md-sort-by="cpu">CPU</md-table-head>
                        <md-table-head md-sort-by="avgCpu">Avg. CPU Usage</md-table-head>
                        <md-table-head md-sort-by="memory">Memory</md-table-head>
                        <md-table-head md-sort-by="cluster">Cluster</md-table-head>
                        <md-table-head md-sort-by="nodeName">Node</md-table-head>
                    </md-table-row>
                </md-table-header>

                <md-table-body>
                    <md-table-row v-for="j in joblist" :key="j.id">
                        <md-table-cell><ib-state :state="j.state"></ib-state></md-table-cell>
                        <md-table-cell>
                            <router-link :to="{name: 'JobDetail', params: {
                                        projectName: encodeURIComponent(project.name),
                                        buildNumber: build.number,
                                        buildRestartCounter: build.restartCounter,
                                        jobName: j.name
                                    }}">
                                {{ j.name }}
                            </router-link>
                        </md-table-cell>
                        <md-table-cell>
                            <ib-date :date="j.startDate"></ib-date>
                        </md-table-cell>
                        <md-table-cell>
                            <ib-duration :start="j.startDate" :end="j.endDate"></ib-duration>
                        </md-table-cell>
                        <md-table-cell><div v-if="j.definition && j.definition.resources">{{ j.definition.resources.limits.cpu }} CPU</div></md-table-cell>
                        <md-table-cell v-if="j.avgCpu"><div>{{ j.avgCpu }} CPU</div></md-table-cell>
                        <md-table-cell v-if="!j.avgCpu"><div>N/A</div></md-table-cell>
                        <md-table-cell><div v-if="j.definition && j.definition.resources">{{ j.definition.resources.limits.memory }} MiB </div></md-table-cell>
                        <md-table-cell v-if="j.definition && j.definition.cluster">{{ j.definition.cluster.name }}</md-table-cell>
                        <md-table-cell v-if="!j.definition || !j.definition.cluster"></md-table-cell>
                        <md-table-cell>{{ j.nodeName }}</md-table-cell>
                    </md-table-row>
                </md-table-body>
            </md-table>
        </md-table-card>
    </div>
</template>

<script>
import _ from 'underscore'

export default {
    name: 'JobList',
    props: ['jobs', 'project', 'build'],
    data: function () {
        return {
            field: null,
            order: 'asc'
        }
    },
    computed: {
        joblist: function () {
            let a = _.sortBy(this.jobs, (j) => {
                if (this.field === 'cpu') {
                    if (j.definition) {
                        return j.definition.resources.limits.cpu
                    } else {
                        return null
                    }
                } else if (this.field === 'memory') {
                    if (j.definition) {
                        return j.definition.resources.limits.memory
                    } else {
                        return null
                    }
                } else if (this.field === 'cluster') {
                    if (j.definition && j.definition.cluster) {
                        return j.definition.cluster.name
                    } else {
                        return null
                    }
                } else if (this.field === 'duration') {
                    if (!j.endDate || !j.startDate) {
                        return null
                    }

                    return j.endDate - j.startDate
                } else {
                    return j[this.field]
                }
            })

            if (this.order === 'desc') {
                a = a.reverse()
            }

            return a
        }
    },
    methods: {
        sort (opt) {
            this.field = opt.name
            this.order = opt.type
        }
    }
}
</script>

<style scoped>
</style>
