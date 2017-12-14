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
                <md-toolbar v-if="$store.state.user" class="md-transparent">
                    <md-button class="md-icon-button" v-on:click="project.builds[0].clearCache()"><md-icon>delete_sweep</md-icon><md-tooltip md-direction="bottom">Clear Cache</md-tooltip></md-button>
                    <md-button class="md-icon-button" v-on:click="triggerBuild()"><md-icon>replay</md-icon><md-tooltip md-direction="bottom">Trigger a new Build</md-tooltip></md-button>
                    <md-button class="md-icon-button" v-on:click="openDialog('confirmDeleteProject')"><md-icon>delete_forever</md-icon><md-tooltip md-direction="bottom">Remove project permanently from InfraBox</md-tooltip></md-button>
                </md-toolbar>
            </md-card-header>
            <md-card-area>
                <md-tabs md-fixed class="md-transparent">
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
                    <md-tab id="build-table" md-label="Builds" md-icon="view_module" :md-options="{new_badge: project.getActiveBuilds().length}" class="widget-container">
                        <ib-build-table :project="project"/>
                    </md-tab>

                    <md-tab v-if="$store.state.user" id="project-settings" md-icon="settings" md-label="Settings">
                        <ib-project-settings :project="project"/>
                    </md-tab>
                </md-tabs>
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
import BuildTable from '../build/BuildTable'
import ProjectSettings from './Settings'
import router from '../../router'

export default {
    name: 'ProjectDetail',
    props: ['projectName'],
    components: {
        'ib-build-table': BuildTable,
        'ib-project-settings': ProjectSettings
    },
    store,
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
.label-with-new-badge{font-weight:bolder}.new-badge{background-color:#23c6c8;color:#fff;padding:4px;border-radius:25%}
</style>
