<template>
    <div id='app'>
        <ib-notifications></ib-notifications>
        <md-toolbar>
            <md-button class="md-icon-button" @click="toggleLeftSidenav">
                <md-icon>menu</md-icon>
            </md-button>
            <div style="width: 110px"><img src="../static/logo_white_on_transparent.png" style="flex: 1"></div>
        </md-toolbar>

        <md-sidenav class="md-left" ref="leftSidenav">
            <md-toolbar class="infrabox-logo">
                <img src="../static/logo_image_only.png">
                <span>InfraBox</span>
            </md-toolbar>

            <md-list>
                <md-list-item>
                    <router-link to="/" style="color: inherit"><span><md-icon><i class="fa fa-th-large fa-fw"></i></md-icon><span class="fix-list">Overview</span></span></router-link>
                </md-list-item>

                <md-list-item>
                    <md-icon><i class="fa fa-fw fa-cubes fa-fw"></i></md-icon>
                    <span>Projects</span>
                    <md-list-expand>
                        <md-list>
                            <md-list-item v-for="project of $store.state.projects" class="md-inset">
                                <router-link :to="{name: 'ProjectDetail', params: {projectName: project.name}}">
                                    <span>
                                        <i v-if="project.isGit()" class="fa fa-github"></i>
                                        <i v-if="!project.isGit()" class="fa fa-home"></i>{{ project.name }}
                                    </span>
                                </router-link>
                            </md-list-item>
                        </md-list>
                    </md-list-expand>
                </md-list-item>

                <md-list-item class="navi-link">
                    <a href="#"
                       class="md-list-item-container md-button"
                       target="_blank">
                        <md-icon><i class="fa fa-book fa-fw"></i></md-icon>
                        <span>Docs</span>
                    </a>
                </md-list-item>

                <md-list-item class="navi-link">
                    <a href="https://github.com/InfraBox/infrabox/issues"
                       class="md-list-item-container md-button"
                       target="_blank">
                        <md-icon><i class="fa fa-bug fa-fw"></i></md-icon>
                        <span>Report Issue</span>
                    </a>
                </md-list-item>

                <md-list-item class="navi-link">
                    <a href="#" class="md-list-item-container md-button" v-on:click="logout()">
                        <md-icon><i class="fa fa-sign-out fa-fw"></i></md-icon>
                        <span>Logout</span>
                    </a>
                </md-list-item>
            </md-list>
        </md-sidenav>
        <router-view/>
    </div>
</template>

<script>
    import store from './store'

    export default {
        name: 'app',
        methods: {
            toggleLeftSidenav () {
                this.$refs.leftSidenav.toggle()
            },
            logout () {
                console.log('logout')
            }
        },
        store
    }
</script>

<style>
    .navi-link .md-list-item-container .md-button {
        padding: 0px;
    }

    .infrabox-logo {
        font-size: 24px;
        display: flex;
        flex-flow: column;
        padding: 16px;
        width: 100%;
    }

    .infrabox-logo img {
        width: 160px;
        margin-bottom: 16px;
    }

    .fix-list{
        margin-left: 30px;
    }

</style>
