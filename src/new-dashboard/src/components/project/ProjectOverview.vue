<template>
    <div v-if="project" class="example-box">
		<md-card>
            <md-table-card>
                <md-card-header>
                    <h3 class="md-title">
                        <span v-if="project.isGit()"><md-icon md-iconset="fa fa-github"></md-icon></span>
                        <span v-if="!project.isGit()"><md-icon md-iconset="fa fa-home"></md-icon></span>
                        <router-link :to="{name: 'ProjectDetail', params: {projectName: project.name}}">{{ project.name }}</router-link>
                    </h3>
                    <h3 class="md-subhead">Subtitle here</h3>
                </md-card-header>
                <md-card-content>
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
                            <md-table-row v-if="project.builds.length != 0">
                                <md-table-cell><ib-state :state="project.builds[0].state"></ib-state>
                                    {{ project.builds[0].number }}.{{ project.builds[0].restartCounter }}
                                </md-table-cell>
                                <md-table-cell v-if="project.isGit()">
                                    {{ project.builds[0].commit.author_name }}
                                </md-table-cell>
                                <md-table-cell v-if="project.isGit()">
                                    {{ project.builds[0].commit.branch }}
                                </md-table-cell>
                                <md-table-cell><ib-date :date="project.builds[0].start_date"></ib-date></md-table-cell>
                                <md-table-cell>
                                    <ib-duration :start="project.builds[0].start_date" :end="project.builds[0].end_date"></ib-duration>
                                </md-table-cell>
                                <md-table-cell v-if="project.isGit()">
                                    <ib-gitjobtype :build="project.builds[0]"></ib-gitjobtype>
                                </md-table-cell>
                            </md-table-row>
                        </md-table-body>
                    </md-table>
                </md-card-content>
            </md-table-card>
		</md-card>
    </div>
</template>

<script>
import BuildTable from '../build/BuildTable'

export default {
    props: ['project'],
    components: {
        'ib-build-table': BuildTable
    }
}
</script>

<style scoped>
    .example-box {
        margin: 16px;
    }

    .md-title {
        position: relative;
        z-index: 3;
    }

    .example-tabs {
        margin-top: -48px;
        @media (max-width: 480px) {
            margin-top: -1px;
            background-color: #fff;
        }
    }

    .label-with-new-badge {
        font-weight: bolder
    }

    .new-badge {
        background-color: red;
        color: #fff;
        padding: 3px;
        border-radius: 3px
    }

</style>
