<template>
    <div v-if="loaded">
        <md-layout md-gutter>
            <md-layout  v-for="project of $store.state.projects" md-column md-gutter md-flex-xsmall="100" md-flex-small="100">
                <md-table-card class="example-box">
                    <ib-overview :key="project.id" :project="project"></ib-overview>
                </md-table-card>
            </md-layout>
        </md-layout>
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
        background-color: white;
    }

    .md-title {
        position: relative;
        z-index: 3;
    }

</style>
