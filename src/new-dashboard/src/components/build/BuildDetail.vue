<template>
    <div v-if="data">
		<md-card class="main-card">
            <md-card-header class="main-card-header" style="padding-bottom: 10px">
                <md-card-header-text>
                    <h3 class="md-title card-title">
                        <router-link :to="{name: 'ProjectDetail', params: {
                            projectName: data.project.name
                        }}">
                            <span v-if="data.project.isGit()"><i class="fa fa-github"></i></span>
                            <span v-if="!data.project.isGit()"><i class="fa fa-home"></i></span>
                            {{ data.project.name }}
                        </router-link>
                        / Build {{ data.build.number }}.{{ data.build.restartCounter }}
                    </h3>
                </md-card-header-text>
                <md-toolbar class="md-transparent">
                    <md-button class="md-icon-button" v-on:click="data.build.abort()"><md-icon>not_interested</md-icon><md-tooltip md-direction="bottom">Stop Build</md-tooltip></md-button>
                    <md-button class="md-icon-button" v-on:click="data.build.restart()"><md-icon>replay</md-icon><md-tooltip md-direction="bottom">Restart Build</md-tooltip></md-button>
                    <md-button class="md-icon-button" v-on:click="data.build.clearCache()"><md-icon>delete_sweep</md-icon><md-tooltip md-direction="bottom">Clear Cache</md-tooltip></md-button>
                </md-toolbar>
            </md-card-header>
            <md-card-content>
                <md-layout>
                    <md-layout md-flex-xsmall="100" md-flex-small="100" md-flex-medium="100" md-flex-large="75">
                        <md-tabs md-fixed class="md-transparent">
                            <md-tab id="build-graph" md-label="Build" md-icon="widgets" class="widget-container">
                                <ib-job-gantt :jobs="data.build.jobs"></ib-job-gantt>
                            </md-tab>

                            <md-tab id="job-list" md-label="Jobs" md-icon="view_list">
                                <ib-job-list :jobs="data.build.jobs" :project="data.project" :build="data.build"></ib-job-list>
                            </md-tab>
                        </md-tabs>
                    </md-layout>
                    <md-layout md-flex-xsmall="100" md-flex-small="100" md-flex-medium="100" md-flex-large="25" md-flex-xlarge="25">
                        <md-list class="md-dense widget-container m-md">
                            <ib-state-big :state="data.build.state"></ib-state-big>
                            <md-list-item class="p-l-md p-r-md p-t-md">
                                <span class="md-body-2"><i class="fa fa-calendar fa-fw p-r-xl" aria-hidden="true"></i>
                                Started</span>
                                <span class="md-list-action">
                                    <ib-date :date="data.build.startDate"></ib-date>
                                </span>
                            </md-list-item>
                            <md-list-item class="p-l-md p-r-md">
                                <span class="md-body-2"><i class="fa fa-clock-o fa-fw p-r-xl" aria-hidden="true"></i>
                                Duration</span>
                                <span class="md-list-action">
                                    <ib-duration :start="data.build.startDate" :end="data.build.endDate">
                                  </ib-duration>
                                </span>
                            </md-list-item>
                            <md-list-item v-if="data.build.commit" class="p-l-md p-r-md">
                                <span class="md-body-2"><i class="fa fa-list-ol fa-fw p-r-xl" aria-hidden="true"></i>
                                Commit</span>
                                <span class="md-list-action">
                                    <ib-commit-sha :sha="data.build.commit.id"></ib-commit-sha>
                                </span>
                            </md-list-item>
                            <md-list-item v-if="data.build.commit" class="p-l-md p-r-md">
                                <span class="md-body-2"><i class="fa fa-user fa-fw p-r-xl" aria-hidden="true"></i>
                                Author</span>
                                <span class="md-list-action">
                                    {{ data.build.commit.author_name }}
                                </span>
                            </md-list-item>
                            <md-list-item v-if="data.build.commit" class="p-l-md p-r-md">
                                <span class="md-body-2"><i class="fa fa-code-fork fa-fw p-r-xl" aria-hidden="true"></i>
                                Branch</span>
                                <span class="md-list-action">
                                    {{ data.build.commit.branch }}
                                </span>
                            </md-list-item>
                            <md-list-item class="p-l-md p-r-md">
                                <span class="md-body-2"><i class="fa fa-shield fa-fw p-r-xl" aria-hidden="true"></i>
                                Badges</span>
                            </md-list-item>
                            <ib-badge :project_id="data.project.id" job_name="myJob" subject="test" status="80%" color="green"></ib-badge>
                            <ib-badge :project_id="data.project.id" job_name="test/InfraBox" subject="Coverage" status="80%" color="yellow"></ib-badge>
                            <ib-badge :project_id="data.project.id" job_name="myJob" subject="test" status="80%" color="green"></ib-badge>
                            <ib-badge :project_id="data.project.id" job_name="myJob" subject="test" status="80%" color="green"></ib-badge>
                        </md-list>
                    </md-layout>
                </md-layout>

            </md-card-content>
		</md-card>
    </div>
</template>

<script>
    import store from '../../store'
    import ProjectService from '../../services/ProjectService'
    import GanttChart from './Gantt'
    import StateBig from '../utils/StateBig'
    import Date from '../utils/Date'
    import Duration from '../utils/Duration'
    import CommitSha from '../utils/CommitSha'
    import JobList from '../job/JobList'
    import Badge from '../utils/Badge'

    export default {
        name: 'BuildDetail',
        props: ['projectName', 'buildNumber', 'buildRestartCounter'],
        components: {
            'ib-job-gantt': GanttChart,
            'ib-state-big': StateBig,
            'ib-date': Date,
            'ib-duration': Duration,
            'ib-commit-sha': CommitSha,
            'ib-job-list': JobList,
            'ib-badge': Badge
        },
        store,
        asyncComputed: {
            data: {
                get () {
                    let project = null
                    return ProjectService
                        .findProjectByName(this.projectName)
                        .then((p) => {
                            project = p
                            return p.getBuild(this.buildNumber, this.buildRestartCounter)
                        })
                        .then((build) => {
                            build._updateState()
                            return {
                                project,
                                build
                            }
                        })
                },
                watch () {
                    // eslint-disable-next-line no-unused-expressions
                    this.projectName
                    // eslint-disable-next-line no-unused-expressions
                    this.buildNumber
                    // eslint-disable-next-line no-unused-expressions
                    this.buildRestartCounter
                }
            }
        }
    }
</script>

<style scoped>
.widget-container {
    width: 98%;
}
</style>
