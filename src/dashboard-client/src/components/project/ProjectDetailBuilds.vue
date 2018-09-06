<template>
    <div v-if="project">
        <ib-project-detail-header :project="project" tabIndex="0">
            <div  class="m-l-md m-r-md m-b-md">
                <ib-build-table :project="project"/>
            </div>
        </ib-project-detail-header>
    </div>
</template>

<script>
import store from '../../store'
import ProjectService from '../../services/ProjectService'
import BuildTable from '../build/BuildTable'
import ProjectDetailHeader from './ProjectDetailHeader'

export default {
    name: 'ProjectDetailBuilds',
    props: ['projectName'],
    components: {
        'ib-build-table': BuildTable,
        'ib-project-detail-header': ProjectDetailHeader
    },
    store,
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
