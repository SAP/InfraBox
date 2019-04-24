<template>
    <div>
        <md-table-card class="overview-card" v-if="$store.state.projects.length">
            <md-table class="min-medium">
                <md-table-header>
                    <md-table-row>
                        <md-table-head></md-table-head>
                        <md-table-head></md-table-head>
                        <md-table-head>Project</md-table-head>
                        <md-table-head>Jobs</md-table-head>
                        <md-table-head>Build</md-table-head>
                        <md-table-head>Started</md-table-head>
                        <md-table-head>Duration</md-table-head>
                    </md-table-row>
                </md-table-header>

                <md-table-body>
                    <md-table-row v-for="project of $store.state.projects" :key="project.id">
                        <md-table-cell width="40px">
                            <span v-if="project.isGit()" style="font-size:150%"><i class="fa fa-fw fa-github"></i></span>
                            <span v-if="!project.isGit()"><i class="fa fa-fw fa-home"></i></span>
                        </md-table-cell>
                        <md-table-cell width="40px">
                            <div v-if="project.builds && project.builds[0]">
                                <ib-state :state="project.builds[0].state"></ib-state>
                            </div>
                        </md-table-cell>
                        <md-table-cell>
                            <router-link :to="{name: 'ProjectDetailBuilds', params: {projectName: encodeURIComponent(project.name)}}" class="m-l-xs">{{ project.name }}</router-link>
                        </md-table-cell>
                        <md-table-cell>{{ project.numQueuedJobs }} / {{ project.numScheduledJobs }} / {{ project.numRunningJobs }}
                            <md-tooltip>{{ project.numQueuedJobs }} queued / {{ project.numScheduledJobs }} scheduled / {{ project.numRunningJobs }} running </md-tooltip>
                        </md-table-cell>
                        <md-table-cell>
                            <div v-if="project.builds && project.builds[0]">
                                {{ project.builds[0].number }}.{{ project.builds[0].restartCounter }}
                            </div>
                        </md-table-cell>
                        <md-table-cell>
                            <div v-if="project.builds && project.builds[0]">
                                <ib-date :date="project.builds[0].startDate"></ib-date>
                            </div>
                        </md-table-cell>
                        <md-table-cell>
                            <div v-if="project.builds && project.builds[0]">
                                <ib-duration :start="project.builds[0].startDate" :end="project.builds[0].endDate"></ib-duration>
                            </div>
                        </md-table-cell>
                    </md-table-row>
                </md-table-body>
            </md-table>
            <router-link to="/addproject/" style="color: inherit">
                <md-button class="md-fab md-fab-bottom-right">
                    <md-icon>add</md-icon>
                </md-button>
            </router-link>
        </md-table-card>

        <md-card class="main-card" v-if="!$store.state.projects.length">
            <md-card-header class="main-card-header">
                <md-card-header-text>
                    <h3 class="md-title card-title">
                        <span><i class="fa fa-handshake-o"></i></span>
                        Welcome to InfraBox!
                    </h3>
                </md-card-header-text>
            </md-card-header>
            <md-card-area class="m-xl">
                <p class="md-body-2">Please set up your first project before you can use the full InfraBox functionality:</p>
                <router-link to="/addproject/" style="color: inherit">
                    <md-button md-theme="running" class="md-raised md-primary m-lg"><i class="fa fa-plus"></i> Add project</md-button>
                </router-link>

                <p class="md-body-2"><i class="fa fa-info-circle text-blue"></i> If you are completely new to InfraBox or need some further information have a look at the <a href="https://github.com/SAP/InfraBox/blob/master/docs/doc.md" target="_blank">documentation</a>.</p>
            </md-card-area>

            <router-link to="/addproject/" style="color: inherit">
                <md-button class="md-fab md-fab-bottom-right">
                    <md-icon>add</md-icon>
                </md-button>
            </router-link>
        </md-card>
    </div>
</template>

<script>
import store from '../store'

export default {
    name: 'InfraBoxOverview',
    store
}
</script>

<style scoped>
    .overview-card {
        margin: 16px;
        background-color: white;
    }

    .md-title {
        position: relative;
        z-index: 3;
    }
</style>
