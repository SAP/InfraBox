<template>
    <div>
        <md-table-card class="clean-card add-overflow">
            <md-table class="min-medium" @sort="sort">
                <md-table-header>
                    <md-table-row>
                        <md-table-head md-sort-by="name">Test</md-table-head>
                        <md-table-head md-sort-by="suite">Suite</md-table-head>
                        <md-table-head md-sort-by="duration">Duration</md-table-head>
                        <md-table-head md-sort-by="state">Result</md-table-head>
                        <md-table-head md-sort-by="timestamp">Timestamp</md-table-head>
                    </md-table-row>
                </md-table-header>

                <md-table-body>
                    <md-table-row v-for="t in tests" :id="t.name+t.suite" :key="t.name+t.suite">
                        <md-table-cell>
                            <router-link :to="{name: 'TestDetail', params: {projectName: project.name, buildNumber: build.number, buildRestartCounter: build.restartCounter, jobName: job.name, testName: t.name, suiteName: t.suite }}">
                                {{ t.name }}
                            </router-link>
                        </md-table-cell>
                        <md-table-cell>{{ t.suite }}</md-table-cell>
                        <md-table-cell>{{ convert(t.duration) }}</md-table-cell>
                        <md-table-cell><ib-state :state="t.state"></ib-state></md-table-cell>
                        <md-table-cell>{{ t.timestamp }}</md-table-cell>
                    </md-table-row>
                </md-table-body>
            </md-table>
            <md-table-pagination
                :md-size="size"
                :md-total="job.tests.length"
                :md-page="page"
                md-label="Tests"
                md-separator="of"
                :md-page-options="[20, 50]"
                @pagination="onPagination">
            </md-table-pagination>
        </md-table-card>
    </div>
</template>

<script>
import _ from 'underscore'
import moment from 'moment'

export default {
    name: 'TestList',
    props: ['job', 'project', 'build'],
    data: () => {
        return {
            tests: [],
            page: 1,
            size: 20
        }
    },
    created () {
        this.job.loadTests().then(() => {
            this.job.tests = _.sortBy(this.job.tests, (j) => { return j['state'] })
            this.onPagination({ size: this.size, page: this.page })
        })
    },
    methods: {
        onPagination (opt) {
            if (this.size !== opt.size) {
                this.page = 1
            } else {
                this.page = opt.page
            }

            this.size = opt.size

            const p = this.page - 1
            const s = p * this.size
            const e = s + this.size

            this.tests = this.job.tests.slice(s, e)
        },
        sort (opt) {
            this.page = 1

            this.job.tests = _.sortBy(this.job.tests, (j) => { return j[opt.name] })

            if (opt.type === 'desc') {
                this.job.tests = this.job.tests.reverse()
            }

            this.onPagination({ size: this.size, page: this.page })
        },
        convert (duration) {
            return moment.utc(duration).format('HH:mm:ss')
        }
    }
}
</script>
