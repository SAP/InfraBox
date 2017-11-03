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
                    <md-menu-item>
                        <span>Edit</span>
                        <md-button class="md-icon-button"><md-icon>mode_edit</md-icon><md-tooltip md-direction="bottom">Edit project</md-tooltip></md-button>
                    </md-menu-item>
                    <md-menu-item v-if="project.builds[0] && project.builds[0].state==='running'" v-on:click="project.builds[0].abort()">
                        <span>Stop Build</span>
                        <md-button class="md-icon-button"><md-icon>not_interested</md-icon><md-tooltip md-direction="bottom">Stop latest build</md-tooltip></md-button>
                    </md-menu-item>
                    <md-menu-item v-if="project.builds[0]" v-on:click="project.builds[0].restart()">
                        <span>Restart Build</span>
                        <md-button class="md-icon-button"><md-icon>replay</md-icon><md-tooltip md-direction="bottom">Restart latest build</md-tooltip></md-button>
                    </md-menu-item>
                    <md-menu-item v-if="project.builds[0]" v-on:click="project.builds[0].clearCache()">
                        <span>Clear Cache</span>
                        <md-button class="md-icon-button"><md-icon>delete_sweep</md-icon><md-tooltip md-direction="bottom">Clear cache of latest build</md-tooltip></md-button>
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
                        <md-table-cell class="md-body-2"><i class="fa fa-fw fa-circle-thin"></i><span style="padding-left: 16px">State</span></md-table-cell>
                        <md-table-cell><ib-state :state="project.builds[0].state" look="small"></ib-state></md-table-cell>
                    </md-table-row>
                    <md-table-row>
                        <md-table-cell class="md-body-2"><i class="fa fa-fw fa-cube"></i><span style="padding-left: 16px">Build</span></md-table-cell>
                        <md-table-cell>
                            {{ project.builds[0].number }}.{{ project.builds[0].restartCounter }}
                        </md-table-cell>
                    </md-table-row>
                    <md-table-row v-if="project.isGit()">
                        <md-table-cell class="md-body-2"><i class="fa fa-fw fa-user"></i><span style="padding-left: 16px">Author</span></md-table-cell>
                        <md-table-cell v-if="project.isGit()">
                            {{ project.builds[0].commit.author_name }}
                        </md-table-cell>
                    </md-table-row>
                    <md-table-row v-if="project.isGit()">
                        <md-table-cell class="md-body-2"><i class="fa fa-fw fa-code-fork"></i><span style="padding-left: 16px">Branch</span></md-table-cell>
                        <md-table-cell v-if="project.isGit()">
                            {{ project.builds[0].commit.branch }}
                        </md-table-cell>
                    </md-table-row>
                    <md-table-row>
                        <md-table-cell class="md-body-2"><i class="fa fa-fw fa-calendar"></i><span style="padding-left: 16px"> Started</span></md-table-cell>
                        <md-table-cell><ib-date :date="project.builds[0].start_date"></ib-date></md-table-cell>
                    </md-table-row>
                    <md-table-row>
                        <md-table-cell class="md-body-2"><i class="fa fa-fw fa-clock-o"></i><span style="padding-left: 16px">Duration</span></md-table-cell>
                        <md-table-cell>
                            <ib-duration :start="project.builds[0].start_date" :end="project.builds[0].end_date"></ib-duration>
                        </md-table-cell>
                    </md-table-row>
                    <md-table-row v-if="project.isGit()">
                        <md-table-cell class="md-body-2"><i class="fa fa-fw fa-file"></i><span style="padding-left: 16px">Type</span></md-table-cell>
                        <md-table-cell v-if="project.isGit()">
                            <ib-gitjobtype :build="project.builds[0]"></ib-gitjobtype>
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
