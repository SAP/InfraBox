<template>
    <div v-if="data">
        <ib-build-detail-header :projectName="projectName" :buildNumber="buildNumber" :buildRestartCounter="buildRestartCounter" tabIndex="1">
            <ib-job-list :jobs="data.build.jobs" :project="data.project" :build="data.build"></ib-job-list>
        </ib-build-detail-header>
    </div>
</template>

<script>
import store from '../../store'
import ProjectService from '../../services/ProjectService'
import JobList from '../job/JobList'
import BuildDetailHeader from './BuildDetailHeader'

export default {
    name: 'BuildDetailJobs',
    store,
    props: ['projectName', 'buildNumber', 'buildRestartCounter'],
    components: {
        'ib-job-list': JobList,
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
