<template>
    <div id='app'>
        <ib-notifications></ib-notifications>
        <md-toolbar>
            <md-button v-if="$store.state.user" class="md-icon-button" @click="toggleLeftSidenav">
                <md-icon>menu</md-icon>
            </md-button>
            <div style="width: 110px">
                <a href="/dashboard/">
                    <img src="../static/logo_white_on_transparent.png" style="flex: 1" />
                </a>
            </div>
            <h2 class="md-title" style="flex: 1"></h2>

            <md-button v-if="$store.state.user && !connected" class="md-button" @click="reconnect" md-right>
                <i class="fa fa-fw fa-bolt"></i> Disconnected
            </md-button>
            <md-button v-if="!$store.state.user" class="md-button" @click="login" md-right>
                <i class="fa fa-sign-in"></i> Login
            </md-button>
            <div v-if="$store.state.user" md-right>
                {{ $store.state.user.username }} | {{ $store.state.settings.INFRABOX_CLUSTER_NAME }}
            </div>
        </md-toolbar>

        <md-sidenav v-if="$store.state.user" class="md-left" ref="leftSidenav">
            <md-toolbar class="infrabox-logo">
                <img src="../static/logo_text_bottom.png">
            </md-toolbar>

            <md-list>
                <md-list-item>
                    <router-link to="/" style="color: inherit">
                        <span @click="toggleLeftSidenav()">
                            <md-icon><i class="fa fa-th-large fa-fw"></i></md-icon>
                            <span class="fix-list">Overview</span>
                        </span>
                    </router-link>
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
                    <a href="https://github.com/SAP/infrabox/tree/master/docs"
                       class="md-list-item-container md-button"
                       target="_blank" @click="toggleLeftSidenav()">
                        <md-icon><i class="fa fa-book fa-fw"></i></md-icon>
                        <span>Docs</span>
                    </a>
                </md-list-item>

                <md-list-item class="navi-link">
                    <a :href="$store.state.settings.INFRABOX_GENERAL_REPORT_ISSUE_URL"
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

                <md-list-item v-if="$store.state.user.hasWriteAccess()">
                    <md-icon><i class="fa fa-fw fa-unlock"></i></md-icon>
                    <span>Admin</span>
                    <md-list-expand>
                        <md-list>
                            <md-list-item class="md-inset">
                                <router-link :to="{name: 'AdminProjects'}">
                                    <span @click="toggleLeftSidenav()">
                                        <i class="fa fa-cubes"></i>
                                        Projects
                                    </span>
                                </router-link>
                            </md-list-item>
                            <md-list-item class="md-inset">
                                <router-link :to="{name: 'AdminUsers'}">
                                    <span @click="toggleLeftSidenav()">
                                        <i class="fa fa-users"></i>
                                        Users
                                    </span>
                                </router-link>
                            </md-list-item>
                            <md-list-item class="md-inset">
                                  <router-link :to="{name: 'AdminClusters'}">
                                      <span @click="toggleLeftSidenav()">
                                          <i class="fa fa-server"></i>
                                          Clusters
                                      </span>
                                  </router-link>
                              </md-list-item>
                        </md-list>
                    </md-list-expand>
                </md-list-item>
            </md-list>
        </md-sidenav>
        <router-view/>
        <md-footer v-if="$store.state.settings.INFRABOX_LEGAL_PRIVACY_URL || $store.state.settings.INFRABOX_LEGAL_TERMS_OF_USE_URL">
            <md-footer-copyright slot="copyright">
                <div class="bg-md md-alignment-center-right p-md text-center">
                    <a class="m-r-lg" target="_blank" rel="noopener noreferrer" v-bind:href="''+$store.state.settings.INFRABOX_LEGAL_PRIVACY_URL"  v-if="$store.state.settings.INFRABOX_LEGAL_PRIVACY_URL">Privacy</a>
                    <a target="_blank" rel="noopener noreferrer" v-bind:href="''+$store.state.settings.INFRABOX_LEGAL_TERMS_OF_USE_URL"  v-if="$store.state.settings.INFRABOX_LEGAL_TERMS_OF_USE_URL">Terms of Use</a>
                </div>
            </md-footer-copyright>
        </md-footer>
    </div>
</template>

<script>
import store from './store'
import router from './router'
import events from './events'
import UserService from './services/UserService'

export default {
    name: 'app',
    data () {
        return {
            connected: true
        }
    },
    store,
    created () {
        events.$on('DISCONNECTED', () => {
            this.connected = false
        })

        events.$on('CONNECTED', () => {
            this.connected = true
        })
    },
    methods: {
        reconnect () {
            window.location.reload(false)
        },
        toggleLeftSidenav () {
            this.$refs.leftSidenav.toggle()
        },
        login () {
            router.push({
                path: '/login',
                query: {redirect: location.href}
            })
        },
        logout () {
            UserService.logout()
            this.toggleLeftSidenav()
            router.push('/login')
        }
    }
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
