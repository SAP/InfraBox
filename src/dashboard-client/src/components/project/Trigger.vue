<template>
    <div v-if="project">
        <md-card class="main-card">
            <md-card-header class="main-card-header">
                <md-card-header-text>
                    <h3 class="md-title card-title">
                        <span v-if="project.isGit()"><i class="fa fa-github"></i></span>
                        <span v-if="!project.isGit()"><i class="fa fa-home"></i></span>
                        {{ project.name }}
                    </h3>
                </md-card-header-text>
            </md-card-header>
            <md-card-area>
                <form novalidate @submit.stop.prevent="submit">
                    <md-input-container>
                        <label>Branch</label>
                        <md-input v-model="branch"></md-input>
                    </md-input-container>
                    <md-input-container>
                        <label>Sha</label>
                        <md-input v-model="sha"></md-input>
                    </md-input-container>
                    <md-button
                        md-theme="default"
                        class="md-raised md-primary"
                        @click="trigger()">Trigger</md-button>
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
        branch: '',
        sha: ''
    }),
    store,
    methods: {
        trigger () {
            this.project.triggerBuild(this.branch, this.sha)
        }
    },
    asyncComputed: {
        project: {
            get () {
                return ProjectService
                    .findProjectByName(this.projectName)
            },
            watch () {
                // eslint-disable-next-line no-unused-expressions
                this.projectName
            }
        }
    }
}
</script>

