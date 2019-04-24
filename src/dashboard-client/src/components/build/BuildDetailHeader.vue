<template>
    <div v-if="build && project">
		<md-card class="main-card">
            <md-card-header class="main-card-header no-padding">
                <md-card-header-text>
                    <h3 class="md-title left-margin">
                        <md-layout>
                            <md-layout md-vertical-align="center">
                                <router-link :to="{name: 'ProjectDetailBuilds', params: {
                                    projectName: project.name
                                }}">
                                    <span v-if="project.isGit()"><i class="fa fa-fw fa-github"></i></span>
                                    <span v-if="!project.isGit()"><i class="fa fa-fw fa-home"></i></span>
                                    {{ project.name }}
                                </router-link>
                                / Build {{ build.number }}.{{ build.restartCounter }}
                            </md-layout>
                            <md-layout md-hide-small md-flex="75" md-align="end" md-vertical-align="start">
                                <md-table-card class="clean-card">
                                    <md-table class="p-xs m-t-sm m-r-xxl m-b-sm">
                                        <md-table-body>
                                            <md-table-row style="border-top: none">
                                                <md-table-cell>
                                                   <ib-state :state="build.state"></ib-state>
                                                </md-table-cell>
                                                <md-table-cell style="text-align: left !important">
                                                    <span><i class="fa fa-calendar fa-fw" aria-hidden="true"></i><strong> Started</strong>
                                                    <ib-date :date="build.startDate"></ib-date></span>
                                                </md-table-cell>
                                                <md-table-cell>
                                                    <span><i class="fa fa-clock-o fa-fw" aria-hidden="true"></i><strong> Duration</strong>
                                                    <ib-duration :start="build.startDate" :end="build.endDate"></ib-duration></span>
                                                </md-table-cell>
                                                <md-table-cell v-if="build.commit">
                                                    <span><i class="fa fa-list-ol fa-fw" aria-hidden="true"></i><strong> Commit</strong>
                                                    <a target="_blank" :href="build.commit.url"><ib-commit-sha :sha="build.commit.id"></ib-commit-sha></a></span>
                                                </md-table-cell>
                                                <md-table-cell v-if="build.commit">
                                                    <span><i class="fa fa-user fa-fw" aria-hidden="true"></i><strong> Author</strong><br/>
                                                    {{ build.commit.author_name }}</span>
                                                </md-table-cell>
                                                <md-table-cell v-if="build.commit">
                                                    <span><i class="fa fa-code-fork fa-fw" aria-hidden="true"></i><strong> Branch</strong><br/>
                                                    {{ build.commit.branch }}</span>
                                                </md-table-cell>
                                        </md-table-row>
                                      </md-table-body>
                                    </md-table>
                                </md-table-card>
                            </md-layout>
                        </md-layout>
                        <md-layout class="m-b-xl" v-if="$store.state.user">
                            <md-layout  md-align="start" md-vertical-align="start" md-flex-xsmall="100" md-flex-small="100" md-flex-medium="100" md-flex-large="100" md-flex-xlarge="100" md-hide-small>
                                <md-button class="md-raised md-primary md-dense" v-on:click="build.abort()">
                                    <md-icon>not_interested</md-icon><span class="m-l-xs">Stop Build</span>
                                    <md-tooltip md-direction="bottom">Stop Build</md-tooltip>
                                </md-button>
                                <md-button class="md-raised md-primary md-dense" v-on:click="build.restart()">
                                    <md-icon>replay</md-icon><span class="m-l-xs">Restart Build</span>
                                    <md-tooltip md-direction="bottom">Restart Build</md-tooltip>
                                </md-button>
                                <md-button class="md-raised md-primary md-dense" v-on:click="build.clearCache()">
                                    <md-icon>delete_sweep</md-icon><span class="m-l-xs">Clear Cache</span>
                                    <md-tooltip md-direction="bottom">Clear Cache</md-tooltip>
                                </md-button>
                            </md-layout>
                            <md-layout  md-align="start" md-vertical-align="start" md-flex-xsmall="100" md-flex-small="100" md-flex-medium="100" md-flex-large="100" md-flex-xlarge="100" md-hide-medium-and-up>
                                <md-table-card class="clean-card">
                                    <md-table>
                                        <md-table-body>
                                            <md-table-row style="border-top: none">
                                                <md-table-cell>
                                                    <div class="m-r-xl">
                                                        <ib-state :state="build.state"></ib-state>
                                                    </div>
                                                    <div class="m-r-xl">
                                                        <md-button class="md-icon-button md-primary md-raised md-dense" v-on:click="build.abort()">
                                                            <md-icon style="color: white">not_interested</md-icon>
                                                            <md-tooltip md-direction="bottom">Stop Build</md-tooltip>
                                                        </md-button>
                                                    </div>
                                                    <div class="m-r-xl">
                                                        <md-button class="md-icon-button md-primary  md-raised md-dense" v-on:click="build.restart()">
                                                            <md-icon style="color: white">replay</md-icon>
                                                            <md-tooltip md-direction="bottom">Restart Build</md-tooltip>
                                                        </md-button>
                                                    </div>
                                                    <div class="m-r-xl">
                                                        <md-button class="md-icon-button md-primary md-raised md-dense" v-on:click="build.clearCache()">
                                                            <md-icon style="color: white">delete_sweep</md-icon>
                                                            <md-tooltip md-direction="bottom">Clear Cache</md-tooltip>
                                                        </md-button>
                                                    </div>
                                                    <div class="m-r-xl">
                                                        <md-menu md-size="4" class="bg-white">
                                                            <md-button class="md-icon-button md-primary md-raised md-dense" md-menu-trigger>
                                                                <md-icon style="color: white">info</md-icon>
                                                                <md-tooltip md-direction="bottom">Show Details</md-tooltip>
                                                            </md-button>
                                                            <md-menu-content class="bg-white">
                                                                <md-menu-item class="bg-white">
                                                                    <span><i class="fa fa-calendar fa-fw" aria-hidden="true"></i><strong> Started</strong>
                                                                    <ib-date :date="build.startDate"></ib-date></span>
                                                                </md-menu-item>
                                                                <md-menu-item class="bg-white">
                                                                    <span><i class="fa fa-clock-o fa-fw" aria-hidden="true"></i><strong> Duration</strong>
                                                                    <ib-duration :start="build.startDate" :end="build.endDate"></ib-duration></span>
                                                                </md-menu-item>
                                                                <md-menu-item class="bg-white" v-if="build.commit">
                                                                    <span><i class="fa fa-list-ol fa-fw" aria-hidden="true"></i><strong> Commit</strong>
                                                                    <a target="_blank" :href="build.commit.url"><ib-commit-sha :sha="build.commit.id"></ib-commit-sha></a></span>
                                                                </md-menu-item>
                                                                <md-menu-item class="bg-white" v-if="build.commit">
                                                                    <span><i class="fa fa-user fa-fw" aria-hidden="true"></i><strong> Author</strong><br/>
                                                                    {{ build.commit.author_name }}</span>
                                                                </md-menu-item>
                                                                <md-menu-item class="bg-white" v-if="build.commit">
                                                                    <span><i class="fa fa-code-fork fa-fw" aria-hidden="true"></i><strong> Branch</strong><br/>
                                                                    {{ build.commit.branch }}</span>
                                                                </md-menu-item>
                                                            </md-menu-content>
                                                        </md-menu>
                                                    </div>
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
    props: ['project', 'build', 'tabIndex'],
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
    methods: {
        tabSelected (index) {
            if (this.index === null) {
                this.index = index
                return
            }

            const projectName = encodeURIComponent(this.project.name)

            if (index === 0) {
                router.push(`/project/${projectName}/build/${this.build.number}/${this.build.restartCounter}`)
            } else {
                router.push(`/project/${projectName}/build/${this.build.number}/${this.build.restartCounter}/jobs`)
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
