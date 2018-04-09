<template>
    <div v-if="build">
        <ib-build-detail-header :project="project" :build="build" tabIndex="0">
            <ib-job-gantt :jobs="build.jobs"></ib-job-gantt>
        </ib-build-detail-header>
    </div>
</template>

<script>
import store from '../../store'
import ProjectService from '../../services/ProjectService'
import GanttChart from './Gantt'
import BuildDetailHeader from './BuildDetailHeader'

export default {
    name: 'BuildDetail',
    store,
    props: ['projectName', 'buildNumber', 'buildRestartCounter'],
    components: {
        'ib-job-gantt': GanttChart,
        'ib-build-detail-header': BuildDetailHeader
    },
    data () {
        return {
            project: null,
            build: null
        }
    },
    asyncComputed: {
        load: {
            get () {
                return ProjectService
                    .findProjectByName(this.projectName)
                    .then((p) => {
                        this.project = p
                        return p.getBuild(this.buildNumber, this.buildRestartCounter)
                    })
                    .then((build) => {
                        build._updateState()
                        this.build = build
                    })
            },
            watch () {
                // eslint-disable-next-line no-unused-expressions
                this.projectName
                // eslint-disable-next-line no-unused-expressions
                this.buildNumber
                // eslint-disable-next-line no-unused-expressions
                this.buildRestartCounter
            }
        }
    }
}
</script>

<style scoped>
</style>
