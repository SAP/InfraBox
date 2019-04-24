<template>
    <div v-if="data">
        <md-card class="main-card">
            <md-card-header class="main-card-header" style="padding-bottom: 10px">
            <md-card-header-text>
                <h3 class="md-title card-title">
                <router-link :to="{name: 'ProjectDetailBuilds', params: {
                    projectName: encodeURIComponent(data.project.name)}}">
                    <span v-if="data.project.isGit()"><i class="fa fa-github"></i></span>
                    <span v-if="!data.project.isGit()"><i class="fa fa-home"></i></span>
                    {{ data.project.name }}
                </router-link>
                / <router-link :to="{name: 'BuildDetailGraph', params: {
                    projectName: encodeURIComponent(data.project.name),
                    buildNumber: data.build.number,
                    buildRestartCounter: data.build.restartCounter
                    }}">
                    Build {{ data.build.number }}.{{ data.build.restartCounter }}
                </router-link>
                / <router-link :to="{name: 'JobDetail', params: {
                    projectName: encodeURIComponent(data.project.name),
                    buildNumber: data.build.number,
                    buildRestartCounter: data.build.restartCounter,
                    jobName: data.job.name
                }}">
                {{ data.job.name}}
                </router-link>
                / {{ data.test.name }}
                </h3>
                <h3 class="md-subhead card-title"><strong>Test suite:</strong> {{ data.test.suite }}</h3>
            </md-card-header-text>
            <md-toolbar class="md-transparent">
                <md-chip class="m-r-sm">{{ data.duration }} {{ data.unit }}</md-chip>
                <ib-state-circle-big :state="data.test.state"></ib-state-circle-big>
            </md-toolbar>
            </md-card-header>
            <md-card-content>
                <md-layout>
                    <md-layout md-flex-xsmall="100" md-flex-small="100" md-flex-medium="100" md-flex-large="100" md-flex-xlarge="100">
                        <div style="width: 100%; margin: 16px">
                            <md-card class="clean-card">
                                <md-card-header>
                                    <h2><i class="fa fa-fw fa-history"></i> Test history</h2>
                                </md-card-header>
                                <md-card-content>
                                    <div id="chart-test-results" class="chart"></div>
                                </md-card-content>
                            </md-card>
                        </div>
                        <div style="width: 100%; margin: 16px">
                            <md-card v-if="data.test.message">
                                <md-card-header class="main-card-header">
                                    <div class="md-title"><i class="fa fa-fw fa-envelope"></i> Message</div>
                                </md-card-header>
                                <md-card-content>
                                    <pre class="p-t-md">{{ data.test.message }}</pre>
                                </md-card-content>
                            </md-card>
                            <md-card v-if="data.test.stack" class="m-b-lg">
                                <md-card-header class="main-card-header">
                                    <div class="md-title"><i class="fa fa-fw fa-bug"></i> Stacktrace</div>
                                </md-card-header>
                                <md-card-content>
                                    <pre class="p-t-md">{{ data.test.stack }}</pre>
                                </md-card-content>
                            </md-card>
                        </div>
                    </md-layout>
                </md-layout>
            </md-card-content>
		</md-card>
    </div>
</template>

<script>
import ProjectService from '../../services/ProjectService'
import StateCircleBig from '../utils/StateCircleBig'
import Date from '../utils/Date'
import Duration from '../utils/Duration'
import store from '../../store'
import tauCharts from 'taucharts'
import 'taucharts/build/development/plugins/tauCharts.legend'
import 'taucharts/build/development/plugins/tauCharts.tooltip'

function getBestUnit (d) {
    if (d < 1000) {
        return 'ms'
    } else if (d < 1000 * 60) {
        return 's'
    } else {
        return 'm'
    }
}

function convertDuration (d, unit) {
    if (unit === 'ms') {
        return d
    } else if (unit === 's') {
        return Math.round(d / 1000)
    } else {
        return Math.round(d / (1000 * 60))
    }
}

export default {
    name: 'JobDetail',
    store,
    props: ['jobName', 'projectName', 'buildNumber', 'buildRestartCounter', 'suiteName', 'testName'],
    components: {
        'ib-state-circle-big': StateCircleBig,
        'ib-date': Date,
        'ib-duration': Duration
    },
    data: () => {
        return {
            history: []
        }
    },
    asyncComputed: {
        data: {
            get () {
                let job = null
                let build = null
                let project = null
                let test = null
                let unit = 'ms'
                let duration = 0
                return ProjectService
                    .findProjectByName(decodeURIComponent(this.projectName))
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
                        test = j.getTest(this.testName, this.suiteName)
                        unit = getBestUnit(test.duration)
                        duration = convertDuration(test.duration, unit)
                        return test.loadHistory()
                    })
                    .then((j) => {
                        this.history = []
                        for (let h of test.history) {
                            this.history.push({
                                'build_number': h.build_number,
                                'duration': convertDuration(h.duration, unit),
                                'result': h.state
                            })
                        }

                        return {
                            project,
                            build,
                            job,
                            test,
                            unit,
                            duration
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
    mounted () {
        let draw = () => {
            const config = {
                plugins: [
                    tauCharts.api.plugins.get('legend')(),
                    tauCharts.api.plugins.get('tooltip')(
                        {
                            fields: ['build_number', 'duration', 'result'],
                            formatters: {
                                build_number: {
                                    label: 'Build Number',
                                    format: (x) => {
                                        return (x)
                                    }
                                },
                                duration: {
                                    label: 'Duration',
                                    format: (x) => {
                                        return (x + ' ' + this.data.unit)
                                    }
                                },
                                result: {
                                    label: 'Test Result',
                                    format: (x) => {
                                        return (x)
                                    }
                                }
                            }
                        })
                ],
                data: this.history,
                type: 'bar',
                x: 'build_number',
                y: 'duration',
                color: 'result',
                guide: {
                    x: {
                        nice: false
                    },
                    color: {
                        brewer: {
                            ok: '#43A047',
                            failure: '#cc5965'
                        }
                    }
                }

            }

            const r = document.getElementById('chart-test-results')

            if (!this.chart && r) {
                this.chart = new tauCharts.Chart(config)
                this.chart.renderTo('#chart-test-results')
            }

            if (this.chart) {
                this.chart.refresh()
            }

            this.redraw = setTimeout(draw, 1000)
        }

        this.redraw = setTimeout(draw, 1000)
    },
    beforeDestroy () {
        clearTimeout(this.redraw)
    }

}
</script>

<style scoped>
.chart {
    width: 100%;
    height: 500px;
    margin: 0;
    padding: 0;
    float: left;
}
</style>
