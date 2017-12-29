<template>
    <div>
        <md-layout md-gutter v-if="$store.state.projects">
            <md-layout  v-for="project of $store.state.projects" :key="project.id" md-column md-gutter md-flex-xsmall="100" md-flex-small="100" md-flex-medium="50" md-flex-large="33">
                <md-table-card class="overview-card">
                    <ib-overview :key="project.id" :project="project"></ib-overview>
                </md-table-card>
            </md-layout>
        </md-layout>
        <md-card class="main-card" v-if="!$store.state.projects">
            <md-card-header class="main-card-header">
                <md-card-header-text>
                    <h3 class="md-title card-title">
                        <span><i class="fa fa-handshake-o"></i></span>
                        Welcome to InfraBox!
                    </h3>
                </md-card-header-text>
            </md-card-header>
            <md-card-area class="m-xl">
                <p class="md-body-2">Please set up your first project before you can use the full InfraBox functionality:</p>
                <md-button md-theme="running" class="md-raised md-primary m-lg"><i class="fa fa-plus"></i> Add project</md-button>

                <p class="md-body-2"><i class="fa fa-info-circle text-blue"></i> If you are completely new to InfraBox or need some further information have a look at the <a href="https://infrabox.ninja/docs/" target="_blank">documentation</a>.</p>
            </md-card-area>
        </md-card>
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
