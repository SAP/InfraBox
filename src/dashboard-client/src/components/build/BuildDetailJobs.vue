<template>
    <div v-if="build">
        <ib-build-detail-header :project="project" :build="build" tabIndex="1">
            <ib-job-list :jobs="build.jobs" :project="project" :build="build"></ib-job-list>
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
    data () {
        return {
            project: null,
            build: null
        }
    },
    asyncComputed: {
        data: {
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
