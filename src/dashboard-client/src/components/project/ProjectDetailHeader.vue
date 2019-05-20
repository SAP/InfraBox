<template>
    <div v-if="project">
        <md-card class="main-card">
            <md-card-header class="main-card-header fix-padding">
                <md-card-header-text>
                    <h3 class="md-title card-title">
                        <md-layout>
                            <md-layout md-vertical-align="center">
                                <span class="p-r-xs" v-if="project.isGit()"><i class="fa fa-fw fa-github"></i></span>
                                <span v-if="!project.isGit()"><i class="fa fa-fw fa-home"></i></span>
                                {{ project.name }}
                            </md-layout>
                        </md-layout>
                        <md-layout v-if="project.userHasDevRights()">
                            <md-layout class="m-t-xl m-r-xxl" md-align="start" md-vertical-align="start" md-flex-xsmall="100" md-flex-small="100" md-flex-medium="100" md-flex-large="100" md-flex-xlarge="100" md-hide-small>
                                <md-button v-if="project.userHasAdminRights()" class="md-raised md-primary md-dense" v-on:click="project.builds[0].clearCache()">
                                    <md-icon>delete_sweep</md-icon><span class="m-l-xs">Clear Cache</span>
                                    <md-tooltip md-direction="bottom">Clear Cache</md-tooltip>
                                </md-button>
                                <md-button v-if="project.userHasDevRights()" class="md-raised md-primary md-dense" v-on:click="triggerBuild()">
                                    <md-icon>replay</md-icon><span class="m-l-xs">Trigger Build</span>
                                    <md-tooltip md-direction="bottom">Triger a new Build</md-tooltip>
                                </md-button>
                                <md-button v-if="project.userHasOwnerRights()" class="md-raised md-primary md-dense" v-on:click="openDialog('confirmDeleteProject')">
                                    <md-icon>delete_forever</md-icon><span class="m-l-xs">Delete Project</span>
                                    <md-tooltip md-direction="bottom">Remove project permanently from InfraBox</md-tooltip>
                                </md-button>
                            </md-layout>
                            <md-layout  v-if="project.userHasDevRights()" md-align="start" md-vertical-align="start" md-flex-xsmall="100" md-flex-small="100" md-flex-medium="100" md-flex-large="100" md-flex-xlarge="100" md-hide-medium-and-up>
                                <md-table-card class="clean-card">
                                    <md-table>
                                        <md-table-body>
                                            <md-table-row style="border-top: none">
                                                <md-table-cell>
                                                    <div class="m-r-xl" v-if="project.userHasAdminRights()">
                                                        <md-button class="md-icon-button md-primary md-raised md-dense" v-on:click="project.builds[0].clearCache()">
                                                            <md-icon style="color: white">delete_sweep</md-icon>
                                                            <md-tooltip md-direction="bottom">Clear Cache</md-tooltip>
                                                        </md-button>
                                                    </div>
                                                    <div class="m-r-xl" v-if="project.userHasDevRights()">
                                                        <md-button class="md-icon-button md-primary  md-raised md-dense" v-on:click="triggerBuild()">
                                                            <md-icon style="color: white">replay</md-icon>
                                                            <md-tooltip md-direction="bottom">Trigger a new Build</md-tooltip>
                                                        </md-button>
                                                    </div>
                                                    <div class="m-r-xl" v-if="project.userHasOwnerRights()">
                                                        <md-button class="md-icon-button md-primary md-raised md-dense" v-on:click="openDialog('confirmDeleteProject')">
                                                            <md-icon style="color: white">delete_forever</md-icon>
                                                            <md-tooltip md-direction="bottom">Remove project permanently from InfraBox</md-tooltip>
                                                        </md-button>
                                                    </div>
                                                </md-table-cell>
                                            </md-table-row>
                                        </md-table-body>
                                    </md-table>
                                </md-table-card>
                            </md-layout>
                        </md-layout>
                    </h3>
                </md-card-header-text>
            </md-card-header>
            <md-card-area>
                <md-tabs md-fixed class="md-transparent" @change="tabSelected">
                    <template slot="header-item" slot-scope="props">
                        <md-icon v-if="props.header.icon">{{ props.header.icon }}</md-icon>
                        <template v-if="props.header.options && props.header.options.new_badge">
                            <span v-if="props.header.label" class="label-with-new-badge">
                                {{ props.header.label }}
                                <span class="new-badge">{{ props.header.options.new_badge }}</span>
                            </span>
                        </template>
                        <template v-else>
                            <span v-if="props.header.label">{{ props.header.label }}</span>
                        </template>
                    </template>
                    <md-tab id="build-table" md-label="Builds" md-icon="view_module" :md-options="{new_badge: project.getActiveBuilds().length}" class="widget-container" :md-active="tabIndex==0">
                    </md-tab>

                    <md-tab v-if="$store.state.user && project.userHasAdminRights()" id="project-settings" md-icon="settings" md-label="Settings" :md-active="tabIndex==1">
                    </md-tab>
                </md-tabs>
                <slot></slot>
            </md-card-area>
        </md-card>
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
import store from '../../store'
import ProjectService from '../../services/ProjectService'
import router from '../../router'

export default {
    name: 'ProjectDetailHeader',
    props: ['project', 'tabIndex'],
    store,
    data () {
        return {
            index: null
        }
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
            router.push('/project/' + encodeURIComponent(this.project.name) + '/trigger')
        },
        tabSelected (index) {
            if (this.index === null) {
                this.index = index
                return
            }

            const projectName = encodeURIComponent(this.project.name)

            if (index === 0) {
                console.log(`/project/${projectName}`)
                router.push(`/project/${projectName}`)
            } else {
                console.log(`/project/${projectName}/settings`)
                router.push(`/project/${projectName}/settings`)
            }
        }
    }
}
</script>

<style scoped>
.example-tabs {
    margin-top: -48px;
    @media (max-width: 480px) {
      margin-top: -1px;
      background-color: #fff;
    }
}

.label-with-new-badge {
    font-weight: bolder
}

.new-badge {
    background-color: #23c6c8;
    color: #fff;
    padding: 4px;
    border-radius: 25%
}

.left-margin {
    margin-left: 25px !important;
}

.fix-padding {
    padding-top: 7px !important;
    padding-bottom: 22px !important;
    padding-left: 0 !important;
}
</style>
