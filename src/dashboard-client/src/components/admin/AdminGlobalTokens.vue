<template>
    <md-card class="main-card">
        <md-card-header class="main-card-header fix-padding">
            <md-card-header-text>
                <h3 class="md-title card-title">
                    <md-layout>
                        <md-layout md-vertical-align="center">Global Tokens (Audit)</md-layout>
                    </md-layout>
                </h3>
            </md-card-header-text>
        </md-card-header>

        <md-table-card class="clean-card">
            <md-table>
                <md-table-header>
                    <md-table-row>
                        <md-table-head>Owner</md-table-head>
                        <md-table-head>Description</md-table-head>
                        <md-table-head>Read</md-table-head>
                        <md-table-head>Write</md-table-head>
                        <md-table-head>Created</md-table-head>
                        <md-table-head>Expires</md-table-head>
                    </md-table-row>
                </md-table-header>
                <md-table-body>
                    <md-table-row v-for="t in tokens" :key="t.id">
                        <md-table-cell>{{ t.owner_username || '-' }}</md-table-cell>
                        <md-table-cell>{{ t.description }}</md-table-cell>
                        <md-table-cell>
                            <md-icon v-if="t.scope_pull" class="md-primary">check</md-icon>
                            <md-icon v-else>close</md-icon>
                        </md-table-cell>
                        <md-table-cell>
                            <md-icon v-if="t.scope_push" class="md-primary">check</md-icon>
                            <md-icon v-else>close</md-icon>
                        </md-table-cell>
                        <md-table-cell>{{ formatDate(t.created_at) }}</md-table-cell>
                        <md-table-cell>{{ formatDate(t.expires_at) }}</md-table-cell>
                    </md-table-row>
                    <md-table-row v-if="tokens.length === 0">
                        <md-table-cell colspan="6">No global tokens found.</md-table-cell>
                    </md-table-row>
                </md-table-body>
            </md-table>
        </md-table-card>
    </md-card>
</template>

<script>
import moment from 'moment'
import store from '../../store'
import AdminService from '../../services/AdminService'

export default {
    name: 'AdminGlobalTokens',
    store,
    data: () => ({
        tokens: []
    }),
    created () {
        AdminService.loadGlobalTokens().then(() => {
            this.tokens = store.state.admin.globalTokens
        })
    },
    methods: {
        formatDate (v) {
            return v ? moment(v).format('YYYY-MM-DD HH:mm:ss') : '-'
        }
    }
}
</script>

<style scoped>
.fix-padding {
    padding-top: 7px !important;
    padding-bottom: 22px !important;
    padding-left: 0 !important;
}
</style>
