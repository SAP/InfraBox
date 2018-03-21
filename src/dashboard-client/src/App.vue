<template>
    <div id='app'>
        <ib-disconnect></ib-disconnect>
        <ib-notifications></ib-notifications>
        <md-toolbar>
            <md-button v-if="$store.state.user" class="md-icon-button" @click="toggleLeftSidenav">
                <md-icon>menu</md-icon>
            </md-button>
            <div style="width: 110px">
                <a href="http://infrabox.net">
                    <img src="../static/logo_white_on_transparent.png" style="flex: 1" />
                </a>
            </div>
            <h2 class="md-title" style="flex: 1"></h2>
            <md-button v-if="!$store.state.user" class="md-button" @click="login" md-right>
                <i class="fa fa-sign-in"></i> Login
            </md-button>
        </md-toolbar>

        <md-sidenav v-if="$store.state.user" class="md-left" ref="leftSidenav">
            <md-toolbar class="infrabox-logo">
                <img src="../static/logo_text_bottom.png">
            </md-toolbar>

            <md-list>
                <md-list-item>
                    <router-link to="/" style="color: inherit"><span @click="toggleLeftSidenav()"><md-icon><i class="fa fa-th-large fa-fw"></i></md-icon><span class="fix-list">Overview</span></span></router-link>
                </md-list-item>

                <md-list-item>
                    <md-icon><i class="fa fa-fw fa-cubes fa-fw"></i></md-icon>
                    <span>Projects</span>
                    <md-list-expand>
                        <md-list>
                            <md-list-item v-for="project of $store.state.projects" class="md-inset" :key="project.id">
                                <router-link :to="{name: 'ProjectDetailBuilds', params: {projectName: encodeURIComponent(project.name)}}">
                                    <span @click="toggleLeftSidenav()">
                                        <i v-if="project.isGit()" class="fa fa-github"></i>
                                        <i v-if="!project.isGit()" class="fa fa-home"></i>{{ project.name }}
                                    </span>
                                </router-link>
                            </md-list-item>
                        </md-list>
                    </md-list-expand>
                </md-list-item>

                <md-list-item class="navi-link">
                    <a href="/docs/"
                       class="md-list-item-container md-button"
                       target="_blank" @click="toggleLeftSidenav()">
                        <md-icon><i class="fa fa-book fa-fw"></i></md-icon>
                        <span>Docs</span>
                    </a>
                </md-list-item>

                <md-list-item class="navi-link">
                    <a href="https://github.com/InfraBox/infrabox/issues"
                       class="md-list-item-container md-button"
                       target="_blank" @click="toggleLeftSidenav()">
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
import router from './router'
import Disconnect from './components/utils/Disconnect'

export default {
    name: 'app',
    components: {
        'ib-disconnect': Disconnect
    },
    methods: {
        toggleLeftSidenav () {
            this.$refs.leftSidenav.toggle()
        },
        login () {
            router.push('/login')
        },
        logout () {
            this.toggleLeftSidenav()
            document.cookie = 'token=; expires=Thu, 01 Jan 1970 00:00:01 GMT; path=/; Max-Age=0'
            router.push('/login')
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
        flex-flow: column !important;
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
