<template>
    <div v-if="project">
        <ib-project-detail-header :projectName="projectName" tabIndex="1">
            <ib-project-settings :project="project"/>
        </ib-project-detail-header>
    </div>
</template>


<script>
import store from '../../store'
import ProjectService from '../../services/ProjectService'
import ProjectSettings from './Settings'
import ProjectDetailHeader from './ProjectDetailHeader'

export default {
    name: 'ProjectDetailSettings',
    props: ['projectName'],
    components: {
        'ib-project-detail-header': ProjectDetailHeader,
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
</style>
