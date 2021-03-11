<template>
    <div>
        <md-card md-theme="white" class="full-height clean-card">
            <md-card-area>
                <md-list class="m-t-md m-b-md">
                    <md-list-item>
                        <md-input-container class="m-r-sm">
                            <label>From Build Number</label>
                            <md-input v-model="form.from"></md-input>
                        </md-input-container>
                        <md-input-container class="m-r-sm">
                            <label>To Build Number</label>
                            <md-input v-model="form.to"></md-input>
                        </md-input-container>
                        <md-input-container class="m-r-sm">
                            <label>Sha</label>
                            <md-input v-model="form.sha"></md-input>
                        </md-input-container>
                        <md-input-container class="m-l-sm">
                            <label>Branch</label>
                            <md-input v-model="form.branch"></md-input>
                        </md-input-container>
                        <md-input-container>
                            <label>Cronjob</label>
                            <md-select name="cronjob" id="cronjob" v-model="form.cronjob">
                                <md-option value="" class="bg-white">Any</md-option>
                                <md-option value="true" class="bg-white">Yes</md-option>
                                <md-option value="false" class="bg-white">No</md-option>
                            </md-select>
                        </md-input-container>
                        <md-input-container>
                            <label>State</label>
                            <md-select name="state" id="state" v-model="form.state">
                                <md-option value="" class="bg-white">Any</md-option>
                                <md-option value="running" class="bg-white">Running</md-option>
                                <md-option value="failure" class="bg-white">Failure</md-option>
                                <md-option value="unstable" class="bg-white">Unstable</md-option>
                                <md-option value="killed" class="bg-white">Killed</md-option>
                                <md-option value="error" class="bg-white">Error</md-option>
                                <md-option value="finished" class="bg-white">Finished</md-option>
                            </md-select>
                        </md-input-container>
                        <md-button class="md-icon-button md-list-action" @click="doSearch()">
                            <md-icon md-theme="running" class="md-primary">search</md-icon>
                            <md-tooltip>Search</md-tooltip>
                        </md-button>
                        <md-button class="md-icon-button md-list-action" @click="resetSearch()">
                            <md-icon md-theme="running" class="md-primary">clear</md-icon>
                            <md-tooltip>Clear</md-tooltip>
                        </md-button>
                    </md-list-item>
                </md-list>
            </md-card-area>
        </md-card>

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
                        <md-table-head>Type</md-table-head>
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
                        <md-table-cell>
                            <ib-gitjobtype :build="b"></ib-gitjobtype>
                        </md-table-cell>
                    </md-table-row>
                </md-table-body>
            </md-table>
            <md-table-pagination v-if="!this.search.search"
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
            total: 0,

            form: {
                from: null,
                to: null,
                sha: null,
                branch: null,
                cronjob: '',
                startDate: null,
                state: ''
            },

            search: {
                from: null,
                to: null,
                sha: null,
                branch: null,
                cronjob: null,
                startDate: null,
                search: false,
                state: null
            }
        }
    },
    computed: {
        builds () {
            if (this.project.builds.length === 0) {
                return []
            }
            const maxBuildNumber = this.project.builds[0].number
            this.total = maxBuildNumber

            const p = this.page - 1
            const to = maxBuildNumber - (p * this.size) + 1
            let from = to - this.size

            if (from < 0) {
                from = 0
            }

            let builds = []
            let foundFrom = maxBuildNumber

            if (this.search.search) {
                this.project.loadBuilds(this.search.from || 0, this.search.to || maxBuildNumber, this.search.sha, this.search.branch, this.search.cronjob, this.size || 10)

                for (let b of this.project.builds) {
                    if (this.search.branch && b.commit && b.commit.branch !== this.search.branch) {
                        continue
                    }

                    if (this.search.sha && b.commit && b.commit.id !== this.search.sha) {
                        continue
                    }

                    if (this.search.cronjob && String(b.isCronjob) !== this.search.cronjob) {
                        continue
                    }

                    if (this.search.state && b.state !== this.search.state) {
                        continue
                    }

                    if (this.search.from && b.number < this.search.from) {
                        continue
                    }

                    if (this.search.to && b.number > this.search.to) {
                        continue
                    }

                    builds.push(b)
                }
            } else {
                for (let b of this.project.builds) {
                    if (from <= b.number && b.number < to) {
                        builds.push(b)

                        if (b.number < foundFrom) {
                            foundFrom = b.number
                        }
                    }
                }

                if (foundFrom !== from) {
                    this.project.loadBuilds(from, to, this.search.sha, this.search.branch, this.search.cronjob, this.size || 10)
                }
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
        },

        resetSearch () {
            this.search.search = false
        },

        doSearch () {
            this.search = {
                from: this.form.from,
                to: this.form.to,
                sha: this.form.sha,
                branch: this.form.branch,
                cronjob: this.form.cronjob,
                state: this.form.state,
                search: true
            }
        }
    }
}
</script>

<style>
.no-shadow {
    box-shadow: 0px 0px 0px #888888;
}
</style>
