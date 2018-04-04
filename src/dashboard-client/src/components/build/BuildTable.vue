<template>
    <div>
        <md-table-card class="clean-card add-overflow">
            <md-table class="min-medium">
                <md-table-header>
                    <md-table-row>
                        <md-table-head>State</md-table-head>
                        <md-table-head>Build</md-table-head>
                        <md-table-head v-if="project.isGit()">Author</md-table-head>
                        <md-table-head v-if="project.isGit()">Branch</md-table-head>
                        <md-table-head>Start Time</md-table-head>
                        <md-table-head>Duration</md-table-head>
                        <md-table-head v-if="project.isGit()">Type</md-table-head>
                    </md-table-row>
                </md-table-header>

                <md-table-body>
                    <md-table-row v-for="b in project.builds" :key="b.id">
                        <md-table-cell>
                            <ib-state :state="b.state"></ib-state>
                        </md-table-cell>
                        <md-table-cell>
                            <router-link :to="{name: 'BuildDetailGraph', params: {
                                projectName: encodeURIComponent(project.name),
                                buildNumber: b.number,
                                buildRestartCounter: b.restartCounter
                            }}">
                                {{ b.number }}.{{ b.restartCounter }}
                            </router-link>
                        </md-table-cell>
                        <md-table-cell v-if="project.isGit()">
                            <span v-if="b.commit">
                                {{ b.commit.author_name }}
                            </span>
                        </md-table-cell>
                        <md-table-cell v-if="project.isGit()">
                            <span v-if="b.commit">
                                {{ b.commit.branch }}
                            </span>
                        </md-table-cell>
                        <md-table-cell><ib-date :date="b.startDate"></ib-date></md-table-cell>
                        <md-table-cell>
                            <ib-duration :start="b.startDate" :end="b.endDate"></ib-duration>
                        </md-table-cell>
                        <md-table-cell v-if="project.isGit()">
                            <span v-if="b.commit">
                                <ib-gitjobtype :build="b"></ib-gitjobtype>
                            </span>
                        </md-table-cell>
                    </md-table-row>
                </md-table-body>
            </md-table>
        </md-table-card>
    </div>
</template>

<script>
export default {
    props: ['project']
}
</script>

<style>
.no-shadow {
    box-shadow: 0px 0px 0px #888888;
}

</style>
