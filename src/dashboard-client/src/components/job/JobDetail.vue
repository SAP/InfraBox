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
                                <router-link :to="{name: 'ProjectDetailList', params: {projectName: data.project.name}}">
                                    <span v-if="data.project.isGit()"><i class="fa fa-github"></i></span>
                                    <span v-if="!data.project.isGit()"><i class="fa fa-home"></i></span>
                                    {{ data.project.name }}
                                </router-link>
                                / <router-link :to="{name: 'BuildDetailGraph', params: {
                                    projectName: data.project.name,
                                    buildNumber: data.build.number,
                                    buildRestartCounter: data.build.restartCounter
                                    }}">
                                    Build {{ data.build.number }}.{{ data.build.restartCounter }}
                                </router-link>
                                / {{ data.job.name}}
                            </md-layout>
                            <md-layout md-hide-large-and-up>
                                <md-menu md-size="3" class="bg-white">
                                    <md-button md-theme="default" class="md-icon-button md-primary" md-menu-trigger>
                                        <md-icon>info</md-icon>
                                    </md-button>
                                    <md-menu-content class="bg-white">
                                        <md-menu-item class="bg-white">
                                            <span><i class="fa fa-calendar fa-fw" aria-hidden="true"></i><strong> Started</strong>
                                            <ib-date :date="data.job.startDate"></ib-date></span>
                                        </md-menu-item>
                                        <md-menu-item class="bg-white">
                                            <span><i class="fa fa-clock-o fa-fw" aria-hidden="true"></i><strong> Duration</strong>
                                            <ib-duration :start="data.job.startDate" :end="data.job.endDate"></ib-duration></span>
                                        </md-menu-item>
                                        <md-menu-item class="bg-white" v-if="data.build.commit">
                                            <span><i class="fa fa-list-ol fa-fw" aria-hidden="true"></i><strong> Change</strong>
                                            <ib-gitjobtype :build="data.build"></ib-gitjobtype></span>
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
                            <md-layout md-hide-medium md-flex="60" md-align="end" md-vertical-align="start">
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
                                                    <ib-duration :start="data.job.startDate" :end="data.job.endDate"></ib-duration></span>
                                                </md-table-cell>
                                                <md-table-cell v-if="data.build.commit">
                                                    <span><i class="fa fa-list-ol fa-fw" aria-hidden="true"></i><strong> Change</strong>
                                                    <ib-gitjobtype :build="data.build" :showTitle="true"></ib-gitjobtype></span>
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
                            <md-layout md-flex="100" md-align="start" md-vertical-align="start">
                                <div class="clean-card">
                                    <ib-badge v-for="b of data.job.badges" :key="b.subject"
                                    :job="data.job"
                                    :subject="b.subject"
                                    :status="b.status"
                                    :color="b.color"></ib-badge>
                                </div>
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
                <md-button class="md-fab md-primary md-mini md-clean" md-fab-trigger v-on:click="data.job.abort()">
                    <md-icon style="color: white">not_interested</md-icon>
                    <md-tooltip md-direction="bottom">Stop Job</md-tooltip>
                </md-button>
                <md-button class="md-fab md-primary md-mini md-clean" md-fab-trigger v-on:click="data.job.restart()">
                    <md-icon style="color: white">replay</md-icon>
                    <md-tooltip md-direction="bottom">Restart Job</md-tooltip>
                </md-button>
                <md-button class="md-fab md-primary md-mini md-clean" v-on:click="data.job.clearCache()">
                    <md-icon style="color: white">delete_sweep</md-icon>
                    <md-tooltip md-direction="bottom">Clear Job</md-tooltip>
                </md-button>
                <md-button class="md-fab md-primary md-mini md-clean" v-on:click="openDialog('cli_dialog')">
                    <md-icon style="color: white">file_download</md-icon>
                    <md-tooltip md-direction="bottom">Run Local</md-tooltip>
                </md-button>
                <md-button class="md-fab md-primary md-mini md-clean" v-on:click="downloadOutput()" :disabled="data.job.state=='running'||data.job.state=='queued'||data.job.state=='scheduled'">
                    <md-icon style="color: white">subtitles</md-icon>
                    <md-tooltip md-direction="bottom">Console Output</md-tooltip>
                </md-button>
                <md-button class="md-fab md-primary md-mini md-clean" v-on:click="downloadDataOutput()" :disabled="data.job.state=='running'||data.job.state=='queued'||data.job.state=='scheduled'">
                    <md-icon style="color: white">insert_drive_file</md-icon>
                    <md-tooltip md-direction="bottom">Data Output</md-tooltip>
                </md-button>
            </md-speed-dial>
            <md-card-content>
                <md-tabs md-fixed class="md-transparent">
                    <md-tab id="console" md-label="Console" md-icon="subtitles" class="widget-container">
                        <ib-console :job="data.job"></ib-console>
                    </md-tab>
                    <md-tab id="test-list" md-icon="multiline_chart" md-label="Tests">
                        <ib-tests :job="data.job" :build="data.build" :project="data.project"></ib-tests>
                    </md-tab>
                    <md-tab id="stats" md-icon="insert_chart" md-label="Stats">
                        <ib-stats :job="data.job"></ib-stats>
                    </md-tab>
                    <md-tab v-for="t in data.job.tabs" :key="t.name" :id="'tab_' + t.name" md-icon="insert_chart" :md-label="t.name">
                        <ib-tab :tab="t"></ib-tab>
                    </md-tab>
                </md-tabs>
            </md-card-content>
		</md-card>
        <md-dialog ref="cli_dialog" width="100%">
            <md-dialog-title>Run it with infraboxcli</md-dialog-title>
            <md-dialog-content class="bg-white">
                <pre>{{ data.runLocalCommand }}</pre>
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
        'ib-tab': Tab
    },
    asyncComputed: {
        data: {
            get () {
                let job = null
                let build = null
                let project = null
                return ProjectService
                    .findProjectByName(this.projectName)
                    .then((p) => {
                        project = p
                        return p.getBuild(this.buildNumber, this.buildRestartCounter)
                    })
                    .then((b) => {
                        build = b
                        return build.getJob(this.jobName)
                    })
                    .then((j) => {
                        job = j
                        job.listenConsole()
                        job.loadBadges()
                        job.loadEnvironment()
                        job.loadTabs()

                        let runLocalCommand = '$ export INFRABOX_CLI_TOKEN=<YOUR_TOKEN> \\\n$ infrabox pull \\\n'
                        for (let env of job.env) {
                            const value = env.value.replace(/\n/g, '\\n')
                            runLocalCommand += '    -e '
                            runLocalCommand += env.name
                            runLocalCommand += '="'
                            runLocalCommand += value
                            runLocalCommand += '" \\\n'
                        }

                        runLocalCommand += '    --job-id ' + job.id

                        return {
                            project,
                            build,
                            job,
                            runLocalCommand
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
                this.jobId
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
            this.data.job.downloadOutput()
        },
        downloadDataOutput () {
            this.data.job.downloadDataOutput()
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
</style>

