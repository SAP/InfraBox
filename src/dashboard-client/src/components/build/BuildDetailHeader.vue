<template>
    <div v-if="data">
		<md-card class="main-card">
            <md-card-header class="main-card-header no-padding">
                <md-card-header-text>
                    <h3 class="md-title left-margin">
                        <md-layout>
                            <md-layout md-hide-medium-and-up md-vertical-align="center" v-if="$store.state.user">
                                <ib-state :state="data.build.state"></ib-state>
                            </md-layout>
                            <md-layout md-vertical-align="center">
                                <router-link :to="{name: 'ProjectDetailList', params: {
                                    projectName: data.project.name
                                }}">
                                    <span v-if="data.project.isGit()"><i class="fa fa-fw fa-github"></i></span>
                                    <span v-if="!data.project.isGit()"><i class="fa fa-fw fa-home"></i></span>
                                    {{ data.project.name }}
                                </router-link>
                                / Build {{ data.build.number }}.{{ data.build.restartCounter }}
                            </md-layout>
                            <md-layout md-hide-medium-and-up>
                                <md-menu md-size="3" class="bg-white" md-hide-small-and-up>
                                    <md-button md-theme="default" class="md-icon-button md-primary" md-menu-trigger>
                                        <md-icon>info</md-icon>
                                    </md-button>
                                    <md-menu-content class="bg-white">
                                        <md-menu-item class="bg-white">
                                            <span><i class="fa fa-calendar fa-fw" aria-hidden="true"></i><strong> Started</strong>
                                            <ib-date :date="data.build.startDate"></ib-date></span>
                                        </md-menu-item>
                                        <md-menu-item class="bg-white">
                                            <span><i class="fa fa-clock-o fa-fw" aria-hidden="true"></i><strong> Duration</strong>
                                            <ib-duration :start="data.build.startDate" :end="data.build.endDate"></ib-duration></span>
                                        </md-menu-item>
                                        <md-menu-item class="bg-white" v-if="data.build.commit">
                                            <span><i class="fa fa-list-ol fa-fw" aria-hidden="true"></i><strong> Commit</strong>
                                            <a target="_blank" :href="data.build.commit.url"><ib-commit-sha :sha="data.build.commit.id"></ib-commit-sha></a></span>
                                        </md-menu-item>
                                        <md-menu-item class="bg-white" v-if="data.build.commit">
                                            <span><i class="fa fa-user fa-fw" aria-hidden="true"></i><strong> Author</strong><br/>
                                            {{ data.build.commit.author_name }}</span>
                                        </md-menu-item>
                                        <md-menu-item class="bg-white" v-if="data.build.commit">
                                            <span><i class="fa fa-code-fork fa-fw" aria-hidden="true"></i><strong> Branch</strong><br/>
                                            {{ data.build.commit.branch }}</span>
                                        </md-menu-item>
                                    </md-menu-content>
                                </md-menu>
                            </md-layout>
                            <md-layout md-hide-small md-flex="75" md-align="end" md-vertical-align="start">
                                <md-table-card class="clean-card">
                                    <md-table v-once class="p-xs m-t-sm m-r-xxl m-b-sm">
                                        <md-table-body>
                                            <md-table-row style="border-top: none">
                                                <md-table-cell v-if="$store.state.user">
                                                    <ib-state :state="data.build.state"></ib-state>
                                                </md-table-cell>
                                                <md-table-cell style="text-align: left !important">
                                                    <span><i class="fa fa-calendar fa-fw" aria-hidden="true"></i><strong> Started</strong>
                                                    <ib-date :date="data.build.startDate"></ib-date></span>
                                                </md-table-cell>
                                                <md-table-cell>
                                                    <span><i class="fa fa-clock-o fa-fw" aria-hidden="true"></i><strong> Duration</strong>
                                                    <ib-duration :start="data.build.startDate" :end="data.build.endDate"></ib-duration></span>
                                                </md-table-cell>
                                                <md-table-cell v-if="data.build.commit">
                                                    <span><i class="fa fa-list-ol fa-fw" aria-hidden="true"></i><strong> Commit</strong>
                                                    <a target="_blank" :href="data.build.commit.url"><ib-commit-sha :sha="data.build.commit.id"></ib-commit-sha></a></span>
                                                </md-table-cell>
                                                <md-table-cell v-if="data.build.commit">
                                                    <span><i class="fa fa-user fa-fw" aria-hidden="true"></i><strong> Author</strong><br/>
                                                    {{ data.build.commit.author_name }}</span>
                                                </md-table-cell>
                                                <md-table-cell v-if="data.build.commit">
                                                    <span><i class="fa fa-code-fork fa-fw" aria-hidden="true"></i><strong> Branch</strong><br/>
                                                    {{ data.build.commit.branch }}</span>
                                                </md-table-cell>
                                        </md-table-row>
                                      </md-table-body>
                                    </md-table>
                                </md-table-card>
                            </md-layout>
                        </md-layout>
                    </h3>
                </md-card-header-text>
            </md-card-header>
            <md-speed-dial md-open="hover" md-direction="bottom" class="md-fab-top-right" md-theme="default">
                <md-button class="md-icon-button md-primary" md-fab-trigger>
                    <md-icon md-icon-morph>more_vert</md-icon>
                    <md-icon>more_vert</md-icon>
                </md-button>
                <md-button class="md-fab md-primary md-mini md-clean" md-fab-trigger v-on:click="data.build.abort()">
                    <md-icon style="color: white">not_interested</md-icon>
                    <md-tooltip md-direction="bottom">Stop Build</md-tooltip>
                </md-button>
                <md-button class="md-fab md-primary md-mini md-clean" md-fab-trigger v-on:click="data.build.restart()">
                    <md-icon style="color: white">replay</md-icon>
                    <md-tooltip md-direction="bottom">Restart Build</md-tooltip>
                </md-button>
                <md-button class="md-fab md-primary md-mini md-clean" v-on:click="data.build.clearCache()">
                    <md-icon style="color: white">delete_sweep</md-icon>
                    <md-tooltip md-direction="bottom">Clear Cache</md-tooltip>
                </md-button>
            </md-speed-dial>
            <md-card-content>
                 <md-tabs md-fixed class="md-transparent" @change="tabSelected">
                    <md-tab id="build-graph" md-label="Build" md-icon="widgets" class="widget-container" :md-active="tabIndex==0"></md-tab>
                    <md-tab id="job-list" md-label="Jobs" md-icon="view_list" :md-active="tabIndex==1"></md-tab>
                </md-tabs>
                <slot></slot>
            </md-card-content>
		</md-card>
    </div>
</template>

<script>
import store from '../../store'
import ProjectService from '../../services/ProjectService'
import GanttChart from './Gantt'
import Date from '../utils/Date'
import Duration from '../utils/Duration'
import CommitSha from '../utils/CommitSha'
import JobList from '../job/JobList'
import Badge from '../utils/Badge'
import router from '../../router'

export default {
    name: 'BuildDetail',
    store,
    props: ['projectName', 'buildNumber', 'buildRestartCounter', 'tabIndex'],
    components: {
        'ib-job-gantt': GanttChart,
        'ib-date': Date,
        'ib-duration': Duration,
        'ib-commit-sha': CommitSha,
        'ib-job-list': JobList,
        'ib-badge': Badge
    },
    data () {
        return {
            index: null
        }
    },
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
    },
    methods: {
        tabSelected (index) {
            if (this.index === null) {
                this.index = index
                return
            }

            console.log(index)
            if (index === 0) {
                router.push(`/project/${this.projectName}/build/${this.buildNumber}/${this.buildRestartCounter}/graph`)
            } else {
                router.push(`/project/${this.projectName}/build/${this.buildNumber}/${this.buildRestartCounter}/jobs`)
            }
        }
    }
}
</script>

<style scoped>
.widget-container {
    width: 100%;
}

.left-margin {
    margin-left: 25px !important;
}
</style>
