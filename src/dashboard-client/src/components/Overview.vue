<template>
    <div>
        <md-layout md-gutter>
            <md-layout  v-for="project of $store.state.projects" :key="project.id" md-column md-gutter md-flex-xsmall="100" md-flex-small="100" md-flex-medium="50" md-flex-large="33">
                <md-table-card class="overview-card">
                    <ib-overview :key="project.id" :project="project"></ib-overview>
                </md-table-card>
            </md-layout>
        </md-layout>
        <router-link to="/addproject/" style="color: inherit">
            <md-button class="md-fab md-fab-bottom-right">
                <md-icon>add</md-icon>
            </md-button>
        </router-link>
    </div>
</template>

<script>
import store from '../store'

export default {
    name: 'ProjectDetail',
    store
}
</script>

<style scoped>
    .overview-card {
        margin: 16px;
        background-color: white;
    }

    .md-title {
        position: relative;
        z-index: 3;
    }

</style>
