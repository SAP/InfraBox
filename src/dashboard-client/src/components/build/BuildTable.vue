<template>
    <div>
        <md-table-card class="clean-card add-overflow">
            <md-table class="min-medium">
                <md-table-header>
                    <md-table-row>
                        <md-table-head>State</md-table-head>
                        <md-table-head>Build</md-table-head>
                        <md-table-head v-if="project.isGit()">Author</md-table-head>
                        <md-table-head v-if="project.isGit()">Branch</md-table-head>
                        <md-table-head>Start Time</md-table-head>
                        <md-table-head>Duration</md-table-head>
                        <md-table-head v-if="project.isGit()">Type</md-table-head>
                    </md-table-row>
                </md-table-header>

                <md-table-body>
                    <md-table-row v-for="b in builds" :key="b.id">
                        <md-table-cell>
                            <ib-state :state="b.state"></ib-state>
                        </md-table-cell>
                        <md-table-cell>
                            <router-link :to="{name: 'BuildDetailGraph', params: {
                                projectName: encodeURIComponent(project.name),
                                buildNumber: b.number,
                                buildRestartCounter: b.restartCounter
                            }}">
                                {{ b.number }}.{{ b.restartCounter }}
                            </router-link>
                        </md-table-cell>
                        <md-table-cell v-if="project.isGit()">
                            <span v-if="b.commit">
                                {{ b.commit.author_name }}
                            </span>
                        </md-table-cell>
                        <md-table-cell v-if="project.isGit()">
                            <span v-if="b.commit">
                                {{ b.commit.branch }}
                            </span>
                        </md-table-cell>
                        <md-table-cell><ib-date :date="b.startDate"></ib-date></md-table-cell>
                        <md-table-cell>
                            <ib-duration :start="b.startDate" :end="b.endDate"></ib-duration>
                        </md-table-cell>
                        <md-table-cell v-if="project.isGit()">
                            <span v-if="b.commit">
                                <ib-gitjobtype :build="b"></ib-gitjobtype>
                            </span>
                        </md-table-cell>
                    </md-table-row>
                </md-table-body>
            </md-table>
            <md-table-pagination
                :md-size="size"
                :md-total="total"
                :md-page="page"
                md-label="Builds"
                md-separator="of"
                :md-page-options="[10, 25, 50]"
                @pagination="onPagination">
            </md-table-pagination>
        </md-table-card>
    </div>
</template>

<script>
export default {
    props: ['project'],
    data: () => {
        return {
            page: 1,
            size: 10,
            total: 0
        }
    },
    computed: {
        builds () {
            if (this.project.builds.length === 0) {
                return
            }
            const maxBuildNumber = this.project.builds[0].number
            this.total = maxBuildNumber

            const p = this.page - 1
            const to = maxBuildNumber - (p * this.size) + 1
            const from = to - this.size

            let builds = []
            let foundFrom = maxBuildNumber
            for (let b of this.project.builds) {
                if (from <= b.number && b.number < to) {
                    builds.push(b)

                    if (b.number < foundFrom) {
                        foundFrom = b.number
                    }
                }
            }

            if (foundFrom !== from) {
                this.project.loadBuilds(from, to)
            }

            return builds
        }
    },
    methods: {
        onPagination (opt) {
            if (this.size !== opt.size) {
                this.page = 1
            } else {
                this.page = opt.page
            }

            this.size = opt.size
        }
    }
}
</script>

<style>
.no-shadow {
    box-shadow: 0px 0px 0px #888888;
}
</style>
