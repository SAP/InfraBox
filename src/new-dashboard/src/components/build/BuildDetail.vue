<template>
  <div v-if="data">
      Build Detail {{ data.project.name }}
  </div>
</template>

<script>
import store from '../../store'
import ProjectService from '../../services/ProjectService'

export default {
    name: 'BuildDetail',
    props: ['projectName', 'buildNumber', 'buildRestartCounter'],
    store,
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
                    .then(function (build) {
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
