<template>
    <div v-if="job">
        <md-card class="main-card">
            <md-card-header class="main-card-header no-padding">
                <md-card-header-text>
                    <h3 class="md-title left-margin">
                        <md-layout>
                            <md-layout md-vertical-align="center">
                                <router-link :to="{name: 'ProjectDetailBuilds', params: {projectName: encodeURIComponent(project.name)}}">
                                    <span v-if="project.isGit()"><i class="fa fa-github"></i></span>
                                    <span v-if="!project.isGit()"><i class="fa fa-home"></i></span>
                                    {{ project.name }}
                                </router-link>
                                / <router-link :to="{name: 'BuildDetailGraph', params: {
                                    projectName: encodeURIComponent(project.name),
                                    buildNumber: build.number,
                                    buildRestartCounter: build.restartCounter
                                    }}">
                                    Build {{ build.number }}.{{ build.restartCounter }}
                                </router-link>
                                / {{ job.name}}
                            </md-layout>
                            <md-layout md-hide-medium md-flex="60" md-align="end" md-vertical-align="start">
                                <md-table-card class="clean-card">
                                    <md-table class="p-xs m-t-sm m-r-xxl m-b-sm">
                                        <md-table-body>
                                            <md-table-row style="border-top: none">
                                                <md-table-cell v-if="$store.state.user">
                                                    <ib-state :state="job.state"></ib-state>
                                                </md-table-cell>
                                                <md-table-cell style="text-align: left !important">
                                                    <span><i class="fa fa-calendar fa-fw" aria-hidden="true"></i><strong> Started</strong>
                                                    <ib-date :date="job.startDate"></ib-date></span>
                                                </md-table-cell>
                                                <md-table-cell>
                                                    <span><i class="fa fa-clock-o fa-fw" aria-hidden="true"></i><strong> Duration</strong>
                                                    <ib-duration :start="job.startDate" :end="job.endDate"></ib-duration></span>
                                                </md-table-cell>
                                                <md-table-cell v-if="build.commit">
                                                    <span><i class="fa fa-list-ol fa-fw" aria-hidden="true"></i><strong> Change</strong>
                                                    <ib-gitjobtype :build="build" :showTitle="true"></ib-gitjobtype></span>
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
                            <md-layout md-flex="100" md-align="start" md-vertical-align="start">
                                <div class="clean-card">
                                    <ib-badge v-for="b of job.badges" :key="b.subject"
                                    :job="job"
                                    :subject="b.subject"
                                    :status="b.status"
                                    :color="b.color"></ib-badge>
                                </div>
                            </md-layout>
                        </md-layout>
                        <md-layout class="m-b-xl" v-if="$store.state.user">
                            <md-layout  md-align="start" md-vertical-align="start" md-flex-xsmall="100" md-flex-small="100" md-flex-medium="100" md-flex-large="100" md-flex-xlarge="100" md-hide-medium>
                                <md-button class="md-raised md-primary md-dense" v-on:click="job.abort()">
                                    <md-icon>not_interested</md-icon><span class="m-l-xs">Stop Job</span>
                                    <md-tooltip md-direction="bottom">Stop Job</md-tooltip>
                                </md-button>
                                <md-button class="md-raised md-primary md-dense" v-on:click="job.restart()">
                                    <md-icon>replay</md-icon><span class="m-l-xs">Restart Job</span>
                                    <md-tooltip md-direction="bottom">Restart Job</md-tooltip>
                                </md-button>
                                <md-button class="md-raised md-primary md-dense" v-on:click="job.clearCache()">
                                    <md-icon>delete_sweep</md-icon><span class="m-l-xs">Clear Cache</span>
                                    <md-tooltip md-direction="bottom">Clear Job</md-tooltip>
                                </md-button>
                                <md-button class="md-raised md-primary md-dense" v-on:click="openDialog('cli_dialog')">
                                    <md-icon>file_download</md-icon><span class="m-l-xs">Run Local</span>
                                    <md-tooltip md-direction="bottom">Run Local</md-tooltip>
                                </md-button>
                                <md-button class="md-raised md-primary md-dense" v-on:click="downloadOutput()" :disabled="!job.hasLogsAvailable&&(job.state=='running'||job.state=='queued'||job.state=='scheduled')">
                                    <md-icon>subtitles</md-icon><span class="m-l-xs">Console Output</span>
                                    <md-tooltip md-direction="bottom">Console Output</md-tooltip>
                                </md-button>
                                <md-button class="md-raised md-primary md-dense" v-on:click="downloadDataOutput()" :disabled="job.state=='running'||job.state=='queued'||job.state=='scheduled'">
                                    <md-icon>insert_drive_file</md-icon><span class="m-l-xs">Data Output</span>
                                    <md-tooltip md-direction="bottom">Data Output</md-tooltip>
                                </md-button>
                                <md-button class="md-raised md-primary md-dense" v-on:click="downloadAllArchive()" :disabled="job.state=='running'||job.state=='queued'||job.state=='scheduled'">
                                    <md-icon>insert_drive_file</md-icon><span class="m-l-xs">All Archive</span>
                                    <md-tooltip md-direction="bottom">All Archive</md-tooltip>
                                </md-button>
                            </md-layout>
                            <md-layout  md-align="start" md-vertical-align="start" md-flex-xsmall="100" md-flex-small="100" md-flex-medium="100" md-flex-large="100" md-flex-xlarge="100" md-hide-large-and-up>
                                <md-table-card class="clean-card">
                                    <md-table>
                                        <md-table-body>
                                            <md-table-row style="border-top: none">
                                                <md-table-cell>
                                                    <div class="m-r-xl" v-if="$store.state.user">
                                                        <ib-state :state="job.state"></ib-state>
                                                    </div>
                                                    <div class="m-r-xl">
                                                        <md-button class="md-icon-button md-primary md-raised md-dense" v-on:click="job.abort()">
                                                            <md-icon style="color: white">not_interested</md-icon>
                                                            <md-tooltip md-direction="bottom">Stop Job</md-tooltip>
                                                        </md-button>
                                                    </div>
                                                    <div class="m-r-xl">
                                                         <md-button class="md-icon-button md-primary md-raised md-dense" v-on:click="job.restart()">
                                                            <md-icon style="color: white">replay</md-icon>
                                                            <md-tooltip md-direction="bottom">Restart Job</md-tooltip>
                                                        </md-button>
                                                    </div>
                                                    <div class="m-r-xl">
                                                        <md-button class="md-icon-button md-primary md-raised md-dense" v-on:click="job.clearCache()">
                                                            <md-icon style="color: white">delete_sweep</md-icon>
                                                            <md-tooltip md-direction="bottom">Clear Job</md-tooltip>
                                                        </md-button>
                                                    </div>
                                                    <div class="m-r-xl">
                                                        <md-button class="md-icon-button md-primary md-raised md-dense" v-on:click="openDialog('cli_dialog')">
                                                            <md-icon style="color: white">file_download</md-icon>
                                                            <md-tooltip md-direction="bottom">Run Local</md-tooltip>
                                                        </md-button>
                                                    </div>
                                                    <div class="m-r-xl">
                                                        <md-button class="md-icon-button md-primary md-raised md-dense" v-on:click="downloadOutput()" :disabled="!job.hasLogsAvailable&&(job.state=='running'||job.state=='queued'||job.state=='scheduled')">
                                                            <md-icon style="color: white">subtitles</md-icon>
                                                            <md-tooltip md-direction="bottom">Console Output</md-tooltip>
                                                        </md-button>
                                                    </div>
                                                    <div class="m-r-xl">
                                                        <md-button class="md-icon-button md-primary md-raised md-dense" v-on:click="downloadDataOutput()" :disabled="job.state=='running'||job.state=='queued'||job.state=='scheduled'">
                                                            <md-icon style="color: white">insert_drive_file</md-icon>
                                                            <md-tooltip md-direction="bottom">Data Output</md-tooltip>
                                                        </md-button>
                                                    </div>
                                                    <div class="m-r-xl">
                                                        <md-button class="md-icon-button md-primary md-raised md-dense" v-on:click="downloadAllArchive()" :disabled="job.state=='running'||job.state=='queued'||job.state=='scheduled'">
                                                            <md-icon style="color: white">insert_drive_file</md-icon>
                                                            <md-tooltip md-direction="bottom">All Archive</md-tooltip>
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
                                                                    <ib-date :date="job.startDate"></ib-date></span>
                                                                </md-menu-item>
                                                                <md-menu-item class="bg-white">
                                                                    <span><i class="fa fa-clock-o fa-fw" aria-hidden="true"></i><strong> Duration</strong>
                                                                    <ib-duration :start="job.startDate" :end="job.endDate"></ib-duration></span>
                                                                </md-menu-item>
                                                                <md-menu-item class="bg-white" v-if="build.commit">
                                                                    <span><i class="fa fa-list-ol fa-fw" aria-hidden="true"></i><strong> Change</strong>
                                                                    <ib-gitjobtype :build="build"></ib-gitjobtype></span>
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
                <md-tabs md-fixed class="md-transparent">
				    <template slot="header-item" scope="props">
						<md-icon v-if="props.header.icon">{{ props.header.icon }}</md-icon>
						<template v-if="props.header.options && props.header.options.new_badge">
						  <span v-if="props.header.label" class="label-with-new-badge">
							{{ props.header.label }}
							<span class="new-badge">{{ props.header.options.new_badge }}</span>
						  </span>
						</template>
						<template v-else>
						  <span v-if="props.header.label">{{ props.header.label }}</span>
						</template>
					</template>
                    <md-tab id="console" md-label="Console" md-icon="subtitles" class="widget-container">
                        <ib-console :job="job"></ib-console>
                    </md-tab>
                    <md-tab id="test-list" md-icon="multiline_chart" md-label="Tests" :md-options="{new_badge: failedTests}">
                        <ib-tests :job="job" :build="build" :project="project"></ib-tests>
                    </md-tab>
                    <md-tab id="stats" md-icon="insert_chart" md-label="Stats">
                        <ib-stats :job="job"></ib-stats>
                    </md-tab>
                    <md-tab id="archive" md-icon="insert_chart" md-label="Archive">
                        <ib-archive :job="job"></ib-archive>
                    </md-tab>
                    <md-tab v-for="t in job.tabs" :key="t.name" :id="'tab_' + t.name" md-icon="insert_chart" :md-label="t.name.replace('.json', '').replace('.xml', '')">
                        <ib-tab :tab="t"></ib-tab>
                    </md-tab>
                </md-tabs>
            </md-card-content>
		</md-card>
        <md-dialog ref="cli_dialog" width="100%">
            <md-dialog-title>Run it with infraboxcli</md-dialog-title>
            <md-dialog-content class="bg-white">
                <pre>{{ runLocalCommand }}</pre>
            </md-dialog-content>
            <md-dialog-actions>
                <md-button class="md-icon-button md-primary" @click="closeDialog('cli_dialog')"><md-icon>close</md-icon></md-button>
            </md-dialog-actions>
        </md-dialog>
    </div>
</template>

<script>
import ProjectService from '../../services/ProjectService'
import StateBig from '../utils/StateBig'
import Date from '../utils/Date'
import Duration from '../utils/Duration'
import Console from './Console'
import Tab from './Tab'
import Stats from './Stats'
import Tests from './TestList'
import Archive from './Archive'
import Badge from '../utils/Badge'
import store from '../../store'

export default {
    name: 'JobDetail',
    store,
    props: ['jobName', 'projectName', 'buildNumber', 'buildRestartCounter'],
    components: {
        'ib-state-big': StateBig,
        'ib-date': Date,
        'ib-duration': Duration,
        'ib-console': Console,
        'ib-badge': Badge,
        'ib-tests': Tests,
        'ib-stats': Stats,
        'ib-tab': Tab,
        'ib-archive': Archive
    },
    watch: {
        '$route' (to, from) {
            this.jobName = to.params.jobName
            this.project = null
            this.build = null
            this.job = null
        }
    },
    data () {
        return {
            build: null,
            project: null,
            job: null,
            runLocalCommand: null,
            failedTests: 0
        }
    },
    asyncComputed: {
        load: {
            get () {
                return ProjectService
                    .findProjectByName(this.projectName)
                    .then((p) => {
                        this.project = p
                        return p.getBuild(this.buildNumber, this.buildRestartCounter)
                    })
                    .then((b) => {
                        this.build = b
                        return b.getJob(this.jobName)
                    })
                    .then((j) => {
                        this.job = j
                        j.loadBadges()
                        j.loadTabs()
                        j.loadArchive()
                        this.runLocalCommand = '$ export INFRABOX_CLI_TOKEN=<YOUR_TOKEN> \n$ infrabox pull --job-id ' + j.id
                        return j.loadTests()
                    })
                    .then(() => {
                        this.failedTests = 0
                        for (let t of this.job.tests) {
                            if (t.state === 'failure' || t.state === 'error') {
                                this.failedTests += 1
                            }
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
                // eslint-disable-next-line no-unused-expressions
                this.jobName
            }
        }
    },
    methods: {
        openDialog (ref) {
            this.$refs[ref].open()
        },
        closeDialog (ref) {
            this.$refs[ref].close()
        },
        downloadOutput () {
            this.job.downloadOutput()
        },
        downloadDataOutput () {
            this.job.downloadDataOutput()
        },
        downloadAllArchive () {
            this.job.downloadAllArchive()
        }
    }
}
</script>

<style scoped>
.widget-container {
    width: 98%;
}
.left-margin {
    margin-left: 25px !important;
}
.label-with-new-badge {
    font-weight: bolder;
}
.new-badge {
    background-color: #b71c1c;
    color: white;
    padding: 3px;
    border-radius: 3px;
}
</style>
