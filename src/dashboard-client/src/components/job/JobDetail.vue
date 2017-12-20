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
                / <router-link :to="{name: 'BuildDetail', params: {
                    projectName: data.project.name,
                    buildNumber: data.build.number,
                    buildRestartCounter: data.build.restartCounter
                    }}">
                    Build {{ data.build.number }}.{{ data.build.restartCounter }}
                </router-link>
                / <!--<router-link :to="{name: 'JobDetail', params: {
                projectName: data.project.name,
                buildNumber: data.build.number,
                buildRestartCounter: data.build.restartCounter,
                jobId: data.job.name
                }}">
                Job
                </router-link>-->
                {{ data.job.name}}
                </h3>
            </md-card-header-text>
            <md-toolbar v-if="$store.state.user" class="md-transparent">
                <md-button class="md-icon-button" v-on:click="data.job.abort()"><md-icon>not_interested</md-icon><md-tooltip md-direction="bottom">Stop Job</md-tooltip></md-button>
                <md-button class="md-icon-button" v-on:click="data.job.restart()"><md-icon>replay</md-icon><md-tooltip md-direction="bottom">Restart Job</md-tooltip></md-button>
                <md-button class="md-icon-button" v-on:click="data.job.clearCache()"><md-icon>delete_sweep</md-icon><md-tooltip md-direction="bottom">Clear Cache</md-tooltip></md-button>
            </md-toolbar>
            </md-card-header>
            <md-card-content>
                <md-layout>
                    <md-layout md-flex-xsmall="100" md-flex-small="100" md-flex-medium="100" md-flex-large="75" md-flex-xlarge="75">
                        <md-tabs md-fixed class="md-transparent">
                            <md-tab id="console" md-label="Console" md-icon="subtitles" class="widget-container">
                                <ib-console :job="data.job"></ib-console>
                            </md-tab>
                            <md-tab id="test-list" md-icon="multiline_chart" md-label="Tests">
                                <ib-tests :job="data.job" :build="data.build" :project="data.project"></ib-tests>
                            </md-tab>
                            <md-tab id="stats" md-icon="insert_chart" md-label="Stats" style="height:500px">
                                <ib-stats :job="data.job"></ib-stats>
                            </md-tab>
                            <md-tab v-for="t in data.job.tabs" :key="t.name" :id="'tab_' + t.name" md-icon="insert_chart" :md-label="t.name">
                                <ib-tab :tab="t"></ib-tab>
                            </md-tab>
                        </md-tabs>
                    </md-layout>
                    <md-layout md-flex-xsmall="100" md-flex-small="100" md-flex-medium="100" md-flex-large="25" md-flex-xlarge="25">
                        <md-list class="md-dense widget-container" style="margin: 16px">
                            <ib-state-big :state="data.job.state"></ib-state-big>
                            <md-list-item class="p-l-md p-r-md p-t-md">
                                <span class="md-body-2"><i class="fa fa-calendar fa-fw p-r-xl" aria-hidden="true"></i>
                                Started</span>
                                <span class="md-list-action">
                                    <ib-date :date="data.job.startDate"></ib-date>
                                </span>
                            </md-list-item>
                            <md-list-item class="p-l-md p-r-md">
                                <span class="md-body-2"><i class="fa fa-clock-o fa-fw p-r-xl" aria-hidden="true"></i>
                                Duration</span>
                                <span class="md-list-action">
                                    <ib-duration :start="data.job.startDate" :end="data.job.endDate">
                                  </ib-duration>
                                </span>
                            </md-list-item>
                            <md-list-item v-if="data.build.commit" class="p-l-md p-r-md">
                                <span class="md-body-2"><i class="fa fa-list-ol fa-fw p-r-xl" aria-hidden="true"></i>Change</span>
                                <ib-gitjobtype :build="data.build"></ib-gitjobtype>

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
                            <md-list-item class="p-l-md p-r-xs">
                                <span class="md-body-2"><i class="fa fa-download fa-fw p-r-xl" aria-hidden="true"></i>
                                Run Local</span>
                                <span class="md-list-action">
                                    <md-button class="md-raised md-dense" @click="openDialog('cli_dialog')">CLI Command</md-button>
                                </span>
                            </md-list-item>
                            <md-list-item class="p-l-md p-r-xs">
                                <span class="md-body-2"><i class="fa fa-file-archive-o fa-fw p-r-xl" aria-hidden="true"></i>
                                Console Output</span>
                                <span class="md-list-action">
                                    <md-button class="md-raised md-dense" @click="downloadOutput()" :disabled="data.job.state=='running'||data.job.state=='queued'||data.job.state=='scheduled'">Download</md-button>
                                </span>
                            </md-list-item>
                            <md-list-item class="p-l-md p-r-xs">
                                <span class="md-body-2"><i class="fa fa-file-archive-o fa-fw p-r-xl" aria-hidden="true"></i>
                                Data Output</span>
                                <span class="md-list-action">
                                    <md-button class="md-raised md-dense" @click="downloadDataOutput()" :disabled="data.job.state=='running'||data.job.state=='queued'||data.job.state=='scheduled'">Download</md-button>
                                </span>
                            </md-list-item>
                            <ib-badge v-for="b of data.job.badges" :key="b.subject"
                                :job="data.job"
                                :subject="b.subject"
                                :status="b.status"
                                :color="b.color">
                            </ib-badge>
                        </md-list>
                    </md-layout>
                </md-layout>
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
</style>

