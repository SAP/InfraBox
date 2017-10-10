<template>
  <div>
    Build Detail {{ project.name }}
  </div>
</template>

<script>
import store from '../../store'

export default {
  name: 'BuildDetail',
  store,
  data: function () {
    return {
      project: {
        name: ''
      }
    }
  },
  props: ['projectName', 'buildNumber', 'buildRestartCounter'],
  created: function () {
    this.project = this.$store.getters.findProjectByNameParam
    console.log(this.project)
  }
}
</script>
