<template>
    <div v-if="project">
        <md-card class="main-card">
            <md-card-header class="main-card-header">
                <md-card-header-text>
                    <h3 class="md-title card-title">
                        <router-link :to="{name: 'ProjectDetailBuilds', params: {
                            projectName: encodeURIComponent(project.name)
                        }}">
                            <span v-if="project.isGit()"><i class="fa fa-github"></i></span>
                            <span v-if="!project.isGit()"><i class="fa fa-home"></i></span>
                            {{ project.name }}
                        </router-link>: Trigger Build
                    </h3>
                </md-card-header-text>
            </md-card-header>
            <md-card-area>
                <form novalidate @submit.stop.prevent="submit" class="m-xl">
                    <div class="md-body-2 p-t-lg m-b-md"><i class="fa fa-fw fa-rocket"></i> Branch or Sha to trigger:</div>
                    <div class="m-l-md m-r-xl">
                        <md-input-container class="m-r-xl">
                            <label>Branch or Sha</label>
                            <md-input required v-model="branch_or_sha"></md-input>
                        </md-input-container>
                    </div>
                    <div v-if="project.type=='github'" class="md-body-2 p-t-lg m-b-md"><i class="fa fa-fw fa-rocket"></i> GitHub branch (only needed when triggering for specific sha):</div>
                    <div v-if="project.type=='github'" class="m-l-md m-r-xl">
                        <md-input-container class="m-r-xl">
                            <label>Branch</label>
                            <md-input required v-model="branch"></md-input>
                        </md-input-container>
                    </div>
                    <md-list md-theme="white" class="m-t-md m-b-md ">
                        <div class="m-t-md m-b-md"><span class="md-body-2"><i class="fa fa-fw fa-sticky-note-o"></i> Environment Variables </span>(optional):</div>
                        <md-list-item class="m-r-xl">
                            <md-input-container class="m-r-sm">
                                <label>Variable Name</label>
                                <md-input v-model="name"></md-input>
                            </md-input-container>
                            <md-input-container class="m-l-sm">
                                <label>Variable Value</label>
                                <md-input v-model="value"></md-input>
                            </md-input-container>
                            <md-button class="md-icon-button md-list-action" @click="addEnvVar()">
                                <md-icon md-theme="running" class="md-primary">add_circle</md-icon>
                                <md-tooltip>Add new environment variable</md-tooltip>
                            </md-button>
                        </md-list-item>
                        <md-list-item  v-for="envVar in envVars" :key="envVar.name" class="m-r-xl">
                            <md-input-container class="m-r-sm">{{ envVar.name }}</md-input-container>
                            <md-input-container class="m-l-sm"><span class="m-l-sm">{{ envVar.value }}</span></md-input-container>
                            <md-button type="submit" class="md-icon-button md-list-action" @click="deleteEnvVar(envVar.name)">
                                <md-icon class="md-primary">delete</md-icon>
                                <md-tooltip>Delete environment variable</md-tooltip>
                            </md-button>
                        </md-list-item>
                    </md-list>
                    <md-button
                        md-theme="running"
                        class="md-raised md-primary"
                        @click="trigger()"><i class="fa fa-fw fa-rocket"></i> Trigger</md-button>
                </form>
            </md-card-area>
        </md-card>
    </div>
</template>


<script>
import store from '../../store'
import ProjectService from '../../services/ProjectService'

export default {
    name: 'TriggerBuild',
    props: ['projectName'],
    data: () => ({
        branch_or_sha: null,
        name: null,
        value: null,
        envVars: [],
        branch: ''
    }),
    store,
    methods: {
        trigger () {
            this.project.triggerBuild(this.branch_or_sha, this.envVars, this.branch)
        },
        deleteEnvVar (id) {
        },
        addEnvVar () {
            const currVariable = {name: this.name, value: this.value}
            this.envVars.push(currVariable)
            this.name = null
            this.value = null
        }
    },
    asyncComputed: {
        project: {
            get () {
                return ProjectService
                    .findProjectByName(decodeURIComponent(this.projectName))
            },
            watch () {
                // eslint-disable-next-line no-unused-expressions
                this.projectName
            }
        }
    }
}
</script>
