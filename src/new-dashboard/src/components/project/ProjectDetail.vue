<template>
    <div v-if="project">
        <md-card class="main-card">
                <div class="md-title" style="margin-top: 25px; margin-left: 25px">
                    <span v-if="project.isGit()"><i class="fa fa-github"></i></span>
                    <span v-if="!project.isGit()"><i class="fa fa-home"></i></span>
                    {{ project.name }}
                </div>
            <md-card-area>
                <md-tabs md-right :md-dynamic-height="false" class="md-transparent example-tabs">
                    <template slot="header-item" scope="props">
                        <md-icon v-if="props.header.icon">{{ props.header.icon }}</md-icon>
                        <template v-if="props.header.options && props.header.options.new_badge">
                            <span v-if="props.header.label" class="label-with-new-badge">{{ props.header.label }}</span>
                            <span class="new-badge">{{ props.header.options.new_badge }}</span>
                        </template>
                        <template v-else>
                            <span v-if="props.header.label">{{ props.header.label }}</span>
                        </template>
                    </template>


                    <md-tab md-label="Builds" md-icon="dashboard" :md-options="{new_badge: project.getActiveBuilds().length}" md-active>
                        <slot>
                            <ib-build-table :project="project"></ib-build-table>
                        </slot>
                    </md-tab>

                    <md-tab class="code-content" md-label="Settings" md-icon="settings">
                        <slot>
                            <ib-project-settings :project="project"></ib-project-settings>
                        </slot>
                    </md-tab>
                </md-tabs>
            </md-card-area>
        </md-card>
    </div>
</template>


<script>
import store from '../../store'
import ProjectService from '../../services/ProjectService'
import BuildTable from '../build/BuildTable'
import ProjectSettings from './Settings'

export default {
    name: 'ProjectDetail',
    props: ['projectName'],
    components: {
        'ib-build-table': BuildTable,
        'ib-project-settings': ProjectSettings
    },
    store,
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
  .md-title {
    position: relative;
    z-index: 3;
  }
  .example-tabs {
    margin-top: -48px;
    @media (max-width: 480px) {
      margin-top: -1px;
      background-color: #fff;
    }
  }
.label-with-new-badge{font-weight:bolder}.new-badge{background-color:red;color:#fff;padding:3px;border-radius:3px}
</style>
