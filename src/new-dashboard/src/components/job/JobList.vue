<template>
    <div v-if="jobs">
        <md-table-card class="clean-card">
            <md-table>
                <md-table-header>
                    <md-table-row>
                        <md-table-head>State</md-table-head>
                        <md-table-head>Job Name</md-table-head>
                        <md-table-head>Started</md-table-head>
                        <md-table-head>Duration</md-table-head>
                        <md-table-head>Machine</md-table-head>
                    </md-table-row>
                </md-table-header>

                <md-table-body>
                    <md-table-row v-for="j in jobs" :key="j.id">
                        <md-table-cell><ib-state :state="j.state"></ib-state></md-table-cell>
                        <md-table-cell>
                            <router-link :to="{name: 'JobDetail', params: {
                                        projectName: project.name,
                                        buildNumber: build.number,
                                        buildRestartCounter: build.restartCounter,
                                        jobId: j.id
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
                        <md-table-cell><div>{{ j.cpu }} CPU / {{ j.memory }} GiB </div></md-table-cell>
                    </md-table-row>
                </md-table-body>
            </md-table>
        </md-table-card>
    </div>
</template>

<script>
export default {
    name: 'JobList',
    props: ['jobs', 'project', 'build']
}
</script>

<style scoped>
</style>

