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
                        <md-button-toggle md-single class="m-xl md-layout">
                            <md-card class="md-button no-shadow" v-for="r of $store.state.user.githubRepos" :key="r.id">
                                <md-card-header>
                                    <md-card-header-text>
                                        <div class="md-title">{{ r.name }}</div>
                                        <div class="md-subhead">{{ r.owner.login }}</div>
                                    </md-card-header-text>

                                    <md-card-media>
                                        <div class="m-t-md">
                                            <md-icon>
                                                <i v-if="r.private" class="fa fa-fw fa-home fa-3x"></i>
                                                <i v-if="!r.private" class="fa fa-fw fa-globe fa-3x"></i>
                                            </md-icon>
                                        </div>
                                    </md-card-media>
                                </md-card-header>
                                <md-card-content>
                                    <md-list>
                                        <md-list-item>
                                            <md-icon class="md-primary"><i class="fa fa-calendar fa-fw"></i></md-icon>
                                            <div class="md-list-text-container">
                                            <span>Created:</span>
                                            <span><ib-date :date="r.created_at"></ib-date></span>
                                            </div>
                                        </md-list-item>
                                        <md-list-item>
                                            <md-icon class="md-primary"><i class="fa fa-tasks fa-fw"></i></md-icon>
                                            <div class="md-list-text-container">
                                            <span>Open issues:</span>
                                            <span>{{ r.open_issues_count }}</span>
                                            </div>
                                        </md-list-item>
                                        <md-list-item>
                                            <md-icon class="md-primary"><i class="fa fa-code-fork fa-fw"></i></md-icon>
                                            <div class="md-list-text-container">
                                            <span>Forks:</span>
                                            <span>{{ r.forks_count }}</span>
                                            </div>
                                        </md-list-item>
                                    </md-list>
                                </md-card-content>
                                <md-card-actions>
                                    <md-button md-theme="default" class="md-raised md-primary" @click="selectGithubRepo(r)">Select</md-button>
                                </md-card-actions>
                            </md-card>
                        </md-button-toggle>
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
        invalidMessage: 'Name required'
    }),
    watch: {
        projName () {
            var nameRegex = /^[A-Za-z0-9-_]+$/

            this.nameValid = nameRegex.test(this.projName)
            console.log(this.nameValid, this.projName)
            if (this.nameValid) {
                this.invalidMessage = 'Valid name'
            } else {
                this.invalidMessage = 'Name required'
            }
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
