<template>
  <div v-if="data">
      Build Detail {{ data.project.name }} {{ data.build.number }}.{{ data.build.restartCounter }}
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
    data () {
      let project = null
      return ProjectService
        .findProjectByName(this.projectName)
        .then((p) => {
          project = p
          return p.getBuild(this.buildNumber, this.restartCounter)
        })
        .then(function (build) {
          console.log(build)
          return {
            project,
            build
          }
        })
    }
  }
}
</script>
