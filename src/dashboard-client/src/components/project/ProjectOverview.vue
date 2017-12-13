<template>
    <div v-if="project">
        <md-card-header>
            <md-card-header-text>
                <div class="md-title">
                    <span v-if="project.isGit()"><i class="fa fa-github"></i></span>
                    <span v-if="!project.isGit()"><i class="fa fa-home"></i></span>
                    <router-link :to="{name: 'ProjectDetail', params: {projectName: project.name}}" class="m-l-xs">{{ project.name }}</router-link>
                </div>
                <md-subheader v-if="project.getActiveBuilds().length===1" style="padding-left=-10px;">Currently one running build.</md-subheader>
                <md-subheader v-if="project.getActiveBuilds().length===0">Currently no running builds.</md-subheader>
                <md-subheader v-if="project.getActiveBuilds().length>1">Currently {{ project.getActiveBuilds().length }} running builds.</md-subheader>
            </md-card-header-text>
            <md-menu md-size="4" md-direction="bottom left">
                <md-button class="md-icon-button md-accent" md-menu-trigger>
                    <md-icon>more_vert</md-icon>
                </md-button>

                <md-menu-content>
                    <md-menu-item v-if="project.builds[0]" v-on:click="project.builds[0].clearCache()">
                        <span>Clear Cache</span>
                        <md-button class="md-icon-button"><md-icon>delete_sweep</md-icon><md-tooltip md-direction="bottom">Clear cache</md-tooltip></md-button>
                    </md-menu-item>
                    <md-menu-item @click="triggerBuild()">
                        <span>Trigger Build</span>
                        <md-button class="md-icon-button"><md-icon>replay</md-icon><md-tooltip md-direction="bottom">Trigger a new build</md-tooltip></md-button>
                    </md-menu-item>
                    <md-menu-item @click="openDialog('confirmDeleteProject')">
                        <span>Delete Project</span>
                        <md-button class="md-icon-button" id="custom"><md-icon>delete_forever</md-icon><md-tooltip md-direction="bottom">Remove project permanently from InfraBox</md-tooltip></md-button>
                    </md-menu-item>
                </md-menu-content>
            </md-menu>
        </md-card-header>
        <md-card-content>
            <md-table>
                <md-table-body v-if="project.builds.length != 0">
                    <md-table-row>
                        <md-table-cell class="md-body-2"><i class="fa fa-fw fa-circle-thin"></i><span class="p-l-md">Jobs</span></md-table-cell>
                        <md-table-cell>{{ project.numQueuedJobs }} / {{ project.numScheduledJobs }} / {{ project.numRunningJobs }}
                            <md-tooltip>{{ project.numQueuedJobs }} queued / {{ project.numScheduledJobs }} scheduled / {{ project.numRunningJobs }} running </md-tooltip></md-table-cell>
                    </md-table-row>

                    <md-table-row>
                        <md-table-cell class="md-body-2"><i class="fa fa-fw fa-circle-thin"></i><span class="p-l-md">State</span></md-table-cell>
                        <md-table-cell><ib-state :state="project.builds[0].state"></ib-state></md-table-cell>
                    </md-table-row>
                    <md-table-row>
                        <md-table-cell class="md-body-2"><i class="fa fa-fw fa-cube"></i><span class="p-l-md">Build</span></md-table-cell>
                        <md-table-cell>
                            {{ project.builds[0].number }}.{{ project.builds[0].restartCounter }}
                        </md-table-cell>
                    </md-table-row>
                    <md-table-row>
                        <md-table-cell class="md-body-2"><i class="fa fa-fw fa-calendar"></i><span class="p-l-md"> Started</span></md-table-cell>
                        <md-table-cell><ib-date :date="project.builds[0].startDate"></ib-date></md-table-cell>
                    </md-table-row>
                    <md-table-row>
                        <md-table-cell class="md-body-2"><i class="fa fa-fw fa-clock-o"></i><span class="p-l-md">Duration</span></md-table-cell>
                        <md-table-cell>
                            <ib-duration :start="project.builds[0].startDate" :end="project.builds[0].endDate"></ib-duration>
                        </md-table-cell>
                    </md-table-row>
                </md-table-body>
            </md-table>
        </md-card-content>
        <md-dialog md-open-from="#custom" md-close-to="#custom" ref="confirmDeleteProject">
            <md-dialog-title><i class="fa fa-fw fa-exclamation-circle" aria-hidden="true"></i><span> Do you really want to delete this project?</span></md-dialog-title>
            <md-dialog-content>Your project will be permanently removed from InfraBox. Your builds and metadata cannot be restored.</md-dialog-content>
                <md-dialog-actions>
                <md-button md-theme="running" class="md-primary" @click="closeDialog('confirmDeleteProject')">Cancel</md-button>
                <md-button md-theme="running" class="md-primary" @click="deleteProject()">Yes, delete</md-button>
            </md-dialog-actions>
        </md-dialog>
    </div>
</template>

<script>
import BuildTable from '../build/BuildTable'
import ProjectService from '../../services/ProjectService'
import router from '../../router'

export default {
    props: ['project'],
    components: {
        'ib-build-table': BuildTable
    },
    methods: {
        openDialog (ref) {
            this.$refs[ref].open()
        },
        closeDialog (ref) {
            this.$refs[ref].close()
        },
        deleteProject () {
            this.closeDialog('confirmDeleteProject')
            ProjectService.deleteProject(this.project.id)
        },
        triggerBuild () {
            router.push(`/project/${this.project.name}/trigger`)
        }
    }
}
</script>

<style scoped>
    .example-box {
        margin: 16px;
    }

    .md-title {
        position: relative;
        z-index: 3;
    }

</style>
