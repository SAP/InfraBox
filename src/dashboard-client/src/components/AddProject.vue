<template>
    <div>
        <md-card class="main-card">
            <md-card-header class="main-card-header">
                    <md-card-header-text>
                        <h3 class="md-title">
                            <i class="fa fa-plus-circle"></i>
                            <span> Add Project</span>
                        </h3>
                    </md-card-header-text>
            </md-card-header>
        <md-stepper @completed="addProject">
            <md-theme md-name="running">
                <md-step :md-editable="true">
                    <h3>Select project type</h3>
                    <div class="m-t-xxl m-b-xxl">
                        <md-button-toggle md-single>
                          <md-button class="md-toggle" @click="type = 'upload'">
                            <i class="fa fa-fw fa-upload"></i><span> Upload</span>
                          </md-button>

                          <md-button v-if="$store.state.settings.INFRABOX_GITHUB_ENABLED" @click="type = 'github'">
                            <i class="fa fa-fw fa-github"></i><span> GitHub</span>
                          </md-button>

                          <md-button v-if="$store.state.settings.INFRABOX_GERRIT_ENABLED" @click="type = 'gerrit'">
                            <i class="fa fa-fw fa-binoculars"></i><span> Gerrit</span>
                          </md-button>
                        </md-button-toggle>
                    </div>
                </md-step>
                <md-step :md-editable="true" md-label="Project Name" :md-error="!nameValid" :md-continue="nameValid" :md-message="invalidMessage">
                    <h3>Please enter your project name</h3>
                    <md-input-container :class="{'md-input-invalid': !nameValid}">
                        <md-input type="text" v-model="projName" required/>
                        <label>Project Name</label>
                    </md-input-container>
                    <div v-if="type=='github'" class="p-t-md">
                        <h3>Select the GitHub repository to connect</h3>
                    </div>
                    <div v-if="$store.state.user && !$store.state.user.hasGithubAccount() && type=='github'">
                        <md-button @click="connectGithubAccount()">Connect GitHub Account</md-button>
                    </div>
                    <div v-if="$store.state.user && $store.state.user.hasGithubAccount() && type=='github'" class="md-layout md-gutter">
                        <md-table-card class="clean-card full-width m-b-xl m-t-lg">
                            <md-table md-sort="repos">
                                <md-table-header>
                                    <md-table-row>
                                    <md-table-head md-sort-by="repository">Repository</md-table-head>
                                    <md-table-head md-sort-by="owner">Owner</md-table-head>
                                    <md-table-head md-sort-by="privacy">Visibility</md-table-head>
                                    <md-table-head md-sort-by="created">Created</md-table-head>
                                    <md-table-head md-sort-by="issues">Open Issues</md-table-head>
                                    <md-table-head md-sort-by="forks">Forks</md-table-head>
                                    <md-table-head>Select</md-table-head>
                                    </md-table-row>
                                </md-table-header>
                                <md-table-body>
                                    <md-table-row v-for="(r, index) of $store.state.user.githubRepos" :key="r.id">
                                        <md-table-cell class="md-body-2">{{ r.name }}</md-table-cell>
                                        <md-table-cell>{{ r.owner.login }}</md-table-cell>
                                        <md-table-cell>
                                            <i v-if="r.private" class="fa fa-fw fa-home fa-2x"></i>
                                            <i v-if="!r.private" class="fa fa-fw fa-globe fa-2x"></i>
                                        </md-table-cell>
                                        <md-table-cell><ib-date :date="r.created_at"></ib-date></md-table-cell>
                                        <md-table-cell>{{ r.open_issues_count }}</md-table-cell>
                                        <md-table-cell>{{ r.forks_count }}</md-table-cell>
                                        <md-table-cell>
                                            <md-radio md-theme="default" v-model="selectRepo" :md-value="index" @change="selectGithubRepo(r)"></md-radio>
                                        </md-table-cell>
                                    </md-table-row>
                                </md-table-body>
                            </md-table>
                        </md-table-card>
                    </div>
                </md-step>
                <md-step>
                   <h3>Select the visibility of your project</h3>
                    <div class="m-t-xxl m-b-xxl">
                        <md-button-toggle md-single>
                          <md-button class="md-toggle" @click="priv = true">
                            <i class="fa fa-fw fa-user"></i><span> Private</span>
                          </md-button>

                          <md-button @click="priv = false">
                            <i class="fa fa-fw fa-users"></i><span> Public</span>
                          </md-button>
                        </md-button-toggle>
                    </div>
                </md-step>
            </md-theme>
        </md-stepper>
        </md-card>
    </div>
</template>

<script>
import ProjectService from '../services/ProjectService'
import UserService from '../services/UserService'
import store from '../store'

export default {
    name: 'AddProject',
    store,
    data: () => ({
        projName: '',
        nameValid: false,
        type: 'upload',
        priv: true,
        githubRepo: null,
        invalidMessage: 'Name required',
        selectRepo: false
    }),
    created () {
        UserService.loadRepos()
    },
    watch: {
        projName () {
            if (this.projName.length < 3) {
                this.invalidMessage = 'Name must be at least 3 characters long'
                return
            }

            var nameRegex = /^[A-Za-z0-9-_/]+$/
            this.nameValid = nameRegex.test(this.projName)
            if (!this.nameValid) {
                this.invalidMessage = 'Only A-Z, a-z, 0-9, "_" and "-" allowed characters'
                return
            }

            this.invalidMessage = 'Valid name'
        }
    },
    methods: {
        addProject () {
            let repoName = ''
            if (this.githubRepo) {
                repoName = this.githubRepo.owner.login + '/' + this.githubRepo.name
            }

            ProjectService.addProject(this.projName, this.priv, this.type, repoName)
        },
        selectGithubRepo (r) {
            this.githubRepo = r
        },
        connectGithubAccount () {
            window.location.href = '/github/auth/connect'
        }
    }
}
</script>

<style scoped>
</style>
