<template>
<div>
    <md-table-card class="no-shadow">
      <md-toolbar>
        <h1 class="md-title">Builds</h1>
      </md-toolbar>

        <md-table>
            <md-table-header>
                <md-table-row>
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
                    <md-table-cell><ib-state :state="b.state"></ib-state>
                        {{ b.number }}.{{ b.restartCounter }}
                    </md-table-cell>
                    <md-table-cell v-if="project.isGit()">
                        {{ b.commit.author_name }}
                    </md-table-cell>
                    <md-table-cell v-if="project.isGit()">
                        {{ b.commit.branch }}
                    </md-table-cell>
                    <md-table-cell><ib-date :date="b.start_date"></ib-date></md-table-cell>
                    <md-table-cell>
                        <ib-duration :start="b.start_date" :end="b.end_date"></ib-duration>
                    </md-table-cell>
                    <md-table-cell v-if="project.isGit()">
                        <ib-gitjobtype :build="b"></ib-gitjobtype>
                    </md-table-cell>
                </md-table-row>
            </md-table-body>
        </md-table>
      <md-table-pagination
        md-size="5"
        md-total="10"
        md-page="1"
        md-label="Rows"
        md-separator="of"
        :md-page-options="false"
        @pagination="onPagination"></md-table-pagination>
    </md-table-card>
</div>
</template>

<script>
export default {
    props: ['project'],
    methods: {
        onPagination (p) {
            console.log(p)
        }
    }
}
</script>

<style>
.no-shadow {
    box-shadow: 0px 0px 0px #888888;
}
</style>
