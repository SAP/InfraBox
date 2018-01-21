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
                    </h3>
                </md-card-header-text>
            </md-card-header>
            <md-speed-dial md-open="hover" md-direction="bottom" class="md-fab-top-right" md-theme="default" v-if="$store.state.user">
                <md-button class="md-icon-button md-primary" md-fab-trigger>
                    <md-icon md-icon-morph>more_vert</md-icon>
                    <md-icon>more_vert</md-icon>
                </md-button>
                <md-button class="md-fab md-primary md-mini md-clean" md-fab-trigger v-on:click="project.builds[0].clearCache()">
                    <md-icon style="color: white">delete_sweep</md-icon>
                    <md-tooltip md-direction="left">Clear Cache</md-tooltip>
                </md-button>
                <md-button class="md-fab md-primary md-mini md-clean" md-fab-trigger v-on:click="triggerBuild()">
                    <md-icon style="color: white">replay</md-icon>
                    <md-tooltip md-direction="left">Trigger a new Build</md-tooltip>
                </md-button>
                <md-button class="md-fab md-primary md-mini md-clean" v-on:click="openDialog('confirmDeleteProject')">
                    <md-icon style="color: white">delete_forever</md-icon>
                    <md-tooltip md-direction="left">Remove project permanently from InfraBox</md-tooltip>
                </md-button>
            </md-speed-dial>
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

                    <md-tab v-if="$store.state.user" id="project-settings" md-icon="settings" md-label="Settings" :md-active="tabIndex==1">
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
    props: ['projectName', 'tabIndex'],
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
            router.push(`/project/${this.project.name}/trigger`)
        },
        tabSelected (index) {
            if (this.index === null) {
                this.index = index
                return
            }

            if (index === 0) {
                router.push(`/project/${this.projectName}`)
            } else {
                router.push(`/project/${this.projectName}/settings`)
            }
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
