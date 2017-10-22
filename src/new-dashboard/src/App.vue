<template>
<div id='app'>
    <ib-notifications></ib-notifications>
    <md-toolbar>
        <md-button class="md-icon-button" @click="toggleLeftSidenav">
            <md-icon>menu</md-icon>
        </md-button>

        <h2 class="md-title" style="flex: 1">InfraBox</h2>
    </md-toolbar>

    <md-sidenav class="md-left" ref="leftSidenav">
        <md-toolbar class="infrabox-logo">
            <img src="../static/logo_image_only.png">
            <span>InfraBox</span>
        </md-toolbar>
        <md-list>
            <md-list-item>
                <router-link to="/">
                    <md-icon><i class="fa fa-th-large"></i></md-icon>
                    <span>Overview</span>
                </router-link>
            </md-list-item>

            <md-list-item class="navi-link">
                <a href="#"
                   class="md-list-item-container md-button"
                   target="_blank">
                    <md-icon><i class="fa fa-book"></i></md-icon>
                    <span>Docs</span>
                </a>
            </md-list-item>

            <md-list-item class="navi-link">
                <a href="https://github.com/InfraBox/infrabox/issues"
                   class="md-list-item-container md-button"
                   target="_blank">
                    <md-icon><i class="fa fa-bug"></i></md-icon>
                    <span>Report Issue</span>
                </a>
            </md-list-item>

            <md-list-item class="navi-link">
                <a href="#" class="md-list-item-container md-button" v-on:click="logout()">
                    <md-icon><i class="fa fa-sign-out"></i></md-icon>
                    <span>Logout</span>
                </a>
            </md-list-item>
        </md-list>
    </md-sidenav>

    <router-view/>
</div>
</template>

<script>
export default {
    name: 'app',
    methods: {
        toggleLeftSidenav () {
            this.$refs.leftSidenav.toggle()
        },
        logout () {
            console.log('logout')
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
        flex-flow: column;
        padding: 16px;
        width: 100%;
    }

    .infrabox-logo img{
        width: 160px;
        margin-bottom: 16px;
    }
</style>
