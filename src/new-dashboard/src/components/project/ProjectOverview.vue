<template>
    <div class="example-box" v-if="project">
                <h3 class="md-title" style="background-color: yellow; padding: 8px">
                    <span v-if="project.isGit()"><md-icon md-iconset="fa fa-github"></md-icon></span>
                    <span v-if="!project.isGit()"><md-icon md-iconset="fa fa-home"></md-icon></span>
                    {{ project.name }}
                </h3>
               <!-- <h3 class="md-subhead" v-if="project.builds[0] && project.builds[0].state === 'finished'"><span>Last build: <ib-state :state="project.builds[1].state"></ib-state></span></h3>-->

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

                    <md-table-body v-if="project.builds[0]">
                        <md-table-row>
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
    </div>
</template>

<script>
/*
    import store from '../../store'
    import ProjectService from '../../services/ProjectService'

    export default {
        name: 'ProjectDetail',
        props: ['projectName'],
        store,
        asyncComputed: {
            project: {
                get () {
                    return ProjectService
                        .findProjectByName(this.projectName)
                },
                watch () {
                    // eslint-disable-next-line no-unused-expressions
                    this.projectName
                }
            }
        }
    }
    */

import BuildTable from './BuildTable'

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

</style>
