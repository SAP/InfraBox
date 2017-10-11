<template>
  <div v-if="loaded">
      <ib-project v-for="project of $store.state.projects" :key="project.id" :project="project"></ib-project>
  </div>
</template>

<script>
import store from '../store'
import ProjectService from '../services/ProjectService'

export default {
    name: 'ProjectDetail',
    store,
    asyncComputed: {
        loaded () {
            return ProjectService
            ._loadProjects().then(() => { return true })
        }
    }
}
</script>
