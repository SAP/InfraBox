<template>
    <div v-if="loaded">
        <md-card class="example-box">
            <div class="md-headline" style="margin:25px"><md-icon md-iconset="fa fa-th-large"></md-icon> Overview</div>
        </md-card>
        <md-card class="example-box" style="background-color: white">
            <ib-overview v-for="project of $store.state.projects" :key="project.id" :project="project"></ib-overview>
        </md-card>
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
