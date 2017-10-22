<template>
  <div v-if="loaded">
      <div class="md-headline" style="margin:25px">
          <md-icon md-iconset="fa fa-th-large"></md-icon>
          Overview
      </div>

      <ib-overview v-for="project of $store.state.projects" :key="project.id" :project="project"></ib-overview>
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
            .loadProjects().then(() => { return true })
        }
    }
}
</script>


<style scoped>
    .example-box {
        margin: 16px;
        background-color: white
    }

    .md-title {
        position: relative;
        z-index: 3;
    }

</style>
