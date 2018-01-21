<template>
    <div v-if="data">
        <ib-build-detail-header :projectName="projectName" :buildNumber="buildNumber" :buildRestartCounter="buildRestartCounter" tabIndex="0">
            <ib-job-gantt :jobs="data.build.jobs"></ib-job-gantt>
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
    asyncComputed: {
        data: {
            get () {
                let project = null
                return ProjectService
                    .findProjectByName(this.projectName)
                    .then((p) => {
                        project = p
                        return p.getBuild(this.buildNumber, this.buildRestartCounter)
                    })
                    .then((build) => {
                        build._updateState()
                        return {
                            project,
                            build
                        }
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
