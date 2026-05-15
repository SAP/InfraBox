<template>
    <div>
        <!-- ===== Global Viewer Tokens ===== -->
        <md-card class="main-card">
            <md-card-header class="main-card-header fix-padding">
                <md-card-header-text>
                    <h3 class="md-title card-title">
                        <md-layout>
                            <md-layout md-vertical-align="center">Global Viewer Tokens</md-layout>
                        </md-layout>
                    </h3>
                </md-card-header-text>
            </md-card-header>

            <!-- Create form -->
            <md-card md-theme="white" class="clean-card">
                <md-card-area>
                    <md-list class="m-t-md m-b-md">
                        <md-list-item>
                            <md-input-container class="m-r-sm" style="flex: 2">
                                <label>Token Description (e.g. "Grafana Read-Only")</label>
                                <md-input v-model="form.description" @keyup.enter.native="createToken"></md-input>
                            </md-input-container>
                            <md-input-container class="m-r-sm" style="flex: 0 0 160px">
                                <label>Validity (days)</label>
                                <md-input v-model.number="form.expiresDays" type="number" min="1" max="3650" placeholder="365"></md-input>
                            </md-input-container>
                            <md-button :disabled="disableAdd" class="md-icon-button md-list-action" @click="createToken">
                                <md-icon md-theme="running" class="md-primary">add_circle</md-icon>
                                <md-tooltip>Create read-only token</md-tooltip>
                            </md-button>
                        </md-list-item>
                    </md-list>
                </md-card-area>
            </md-card>

            <!-- Token list -->
            <md-table-card class="clean-card">
                <md-table>
                    <md-table-header>
                        <md-table-row>
                            <md-table-head>Description</md-table-head>
                            <md-table-head>Created</md-table-head>
                            <md-table-head>Expires</md-table-head>
                            <md-table-head>Actions</md-table-head>
                        </md-table-row>
                    </md-table-header>
                    <md-table-body>
                        <template v-for="t in tokens">
                            <md-table-row :key="t.id">
                                <md-table-cell>{{ t.description }}</md-table-cell>
                                <md-table-cell>{{ formatDate(t.created_at) }}</md-table-cell>
                                <md-table-cell>
                                    <span :class="expiryClass(t.expires_at)">
                                        {{ formatDate(t.expires_at) }}
                                        <md-icon v-if="isExpiringSoon(t.expires_at)" style="font-size:16px;vertical-align:middle">warning</md-icon>
                                    </span>
                                </md-table-cell>
                                <md-table-cell>
                                    <md-button class="md-icon-button" @click="toggleLog(t)">
                                        <md-icon>history</md-icon>
                                        <md-tooltip>{{ expandedId === t.id ? 'Hide' : 'Show' }} access log</md-tooltip>
                                    </md-button>
                                    <md-button class="md-icon-button" @click="confirmRevoke(t)">
                                        <md-icon class="md-primary">delete</md-icon>
                                        <md-tooltip>Revoke token</md-tooltip>
                                    </md-button>
                                </md-table-cell>
                            </md-table-row>

                            <!-- Inline access log -->
                            <md-table-row v-if="expandedId === t.id" :key="t.id + '-log'" class="log-row">
                                <md-table-cell colspan="3" class="log-cell">
                                    <div v-if="logLoading" class="log-loading">Loading...</div>
                                    <div v-else-if="accessLog.length === 0" class="log-empty">No access records yet.</div>
                                    <table v-else class="log-table">
                                        <thead>
                                            <tr>
                                                <th>Time</th>
                                                <th>Method</th>
                                                <th>Path</th>
                                                <th>Status</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            <tr v-for="(entry, idx) in accessLog" :key="idx">
                                                <td class="log-time">{{ formatDate(entry.accessed_at) }}</td>
                                                <td>{{ entry.method }}</td>
                                                <td class="log-path">{{ entry.path }}</td>
                                                <td>{{ entry.status_code }}</td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </md-table-cell>
                            </md-table-row>
                        </template>

                        <md-table-row v-if="tokens.length === 0">
                            <md-table-cell colspan="4">No personal tokens yet. Create one above.</md-table-cell>
                        </md-table-row>
                    </md-table-body>
                </md-table>
            </md-table-card>
        </md-card>

        <!-- ===== Project Tokens ===== -->
        <md-card class="main-card" style="margin-top: 16px">
            <md-card-header class="main-card-header fix-padding">
                <md-card-header-text>
                    <h3 class="md-title card-title">
                        <md-layout>
                            <md-layout md-vertical-align="center">Project Tokens</md-layout>
                            <md-layout md-vertical-align="center">
                                <small class="section-hint">Manage individual project tokens in each project's settings</small>
                            </md-layout>
                        </md-layout>
                    </h3>
                </md-card-header-text>
            </md-card-header>

            <md-table-card class="clean-card">
                <md-table>
                    <md-table-header>
                        <md-table-row>
                            <md-table-head>Project</md-table-head>
                            <md-table-head>Description</md-table-head>
                            <md-table-head>Read</md-table-head>
                            <md-table-head>Write</md-table-head>
                        </md-table-row>
                    </md-table-header>
                    <md-table-body>
                        <template v-for="project in adminProjects">
                            <md-table-row
                                v-for="token in (project.tokens || [])"
                                :key="project.id + '-' + token.id">
                                <md-table-cell>
                                    <router-link
                                        :to="{name: 'ProjectDetailSettings', params: {projectName: encodeURIComponent(project.name)}}"
                                        style="color: inherit">
                                        {{ project.name }}
                                    </router-link>
                                </md-table-cell>
                                <md-table-cell>{{ token.description }}</md-table-cell>
                                <md-table-cell>
                                    <md-icon v-if="token.scope_pull" class="md-primary">check</md-icon>
                                    <md-icon v-else>close</md-icon>
                                </md-table-cell>
                                <md-table-cell>
                                    <md-icon v-if="token.scope_push" class="md-primary">check</md-icon>
                                    <md-icon v-else>close</md-icon>
                                </md-table-cell>
                            </md-table-row>
                        </template>

                        <md-table-row v-if="projectTokensLoading">
                            <md-table-cell colspan="4">Loading...</md-table-cell>
                        </md-table-row>
                        <md-table-row v-else-if="totalProjectTokenCount === 0">
                            <md-table-cell colspan="4">No project tokens found.</md-table-cell>
                        </md-table-row>
                    </md-table-body>
                </md-table>
            </md-table-card>
        </md-card>

        <!-- New token dialog -->
        <md-dialog ref="tokenDialog">
            <md-dialog-title>Token Created</md-dialog-title>
            <md-dialog-content>
                Save this token somewhere safe — it will not be shown again.<br><br>
                <pre class="token-pre">{{ newToken }}</pre><br>
                Use it with infraboxcli:<br>
                <pre>$ export INFRABOX_CLI_TOKEN=&lt;TOKEN_VALUE&gt;</pre>
            </md-dialog-content>
            <md-dialog-actions>
                <md-button class="md-primary" @click="$refs['tokenDialog'].close()">OK</md-button>
            </md-dialog-actions>
        </md-dialog>

        <!-- Revoke confirmation dialog -->
        <md-dialog-confirm
            ref="revokeDialog"
            md-title="Revoke Token"
            :md-content="`Revoke &quot;${pendingRevoke ? pendingRevoke.description : ''}&quot;? This cannot be undone.`"
            md-ok-text="Revoke"
            md-cancel-text="Cancel"
            @close="onRevokeClose">
        </md-dialog-confirm>
    </div>
</template>

<script>
import moment from 'moment'
import UserTokenService from '../../services/UserTokenService'
import NotificationService from '../../services/NotificationService'
import Notification from '../../models/Notification'

export default {
    name: 'UserGlobalTokens',
    data: () => ({
        tokens: [],
        newToken: '',
        pendingRevoke: null,
        expandedId: null,
        accessLog: [],
        logLoading: false,
        projectTokensLoading: false,
        form: {
            description: '',
            expiresDays: 365
        }
    }),

    computed: {
        disableAdd () {
            return !this.form.description || this.form.description.length < 3 ||
                !this.form.expiresDays || this.form.expiresDays < 1 || this.form.expiresDays > 3650
        },
        adminProjects () {
            return this.$store.state.projects.filter(p => p.userHasAdminRights())
        },
        totalProjectTokenCount () {
            return this.adminProjects.reduce((sum, p) => sum + (p.tokens ? p.tokens.length : 0), 0)
        }
    },

    created () {
        UserTokenService.loadTokens().then((tokens) => {
            this.tokens = tokens
        }).catch(() => {})

        const adminProjects = this.$store.state.projects.filter(p => p.userHasAdminRights())
        if (adminProjects.length > 0) {
            this.projectTokensLoading = true
            Promise.all(adminProjects.map(p => p._loadTokens()))
                .finally(() => { this.projectTokensLoading = false })
        }
    },

    methods: {
        formatDate (v) {
            return v ? moment(v).format('YYYY-MM-DD HH:mm:ss') : '-'
        },

        isExpiringSoon (expiresAt) {
            if (!expiresAt) return false
            return moment(expiresAt).diff(moment(), 'days') <= 30
        },

        expiryClass (expiresAt) {
            if (!expiresAt) return ''
            const days = moment(expiresAt).diff(moment(), 'days')
            if (days < 0) return 'expiry-expired'
            if (days <= 30) return 'expiry-soon'
            return ''
        },

        createToken () {
            if (this.disableAdd) return
            const days = this.form.expiresDays || 365
            UserTokenService.createToken(this.form.description, false, true, days)
                .then((result) => {
                    const expiresAt = new Date()
                    expiresAt.setDate(expiresAt.getDate() + days)
                    this.tokens.unshift({
                        id: result.id,
                        description: result.description,
                        created_at: new Date().toISOString(),
                        expires_at: expiresAt.toISOString()
                    })
                    this.newToken = result.token
                    this.$refs['tokenDialog'].open()
                    this.form.description = ''
                    this.form.expiresDays = 365
                })
                .catch(() => {})
        },

        confirmRevoke (token) {
            this.pendingRevoke = token
            this.$refs['revokeDialog'].open()
        },

        onRevokeClose (type) {
            if (type !== 'ok' || !this.pendingRevoke) {
                this.pendingRevoke = null
                return
            }
            const target = this.pendingRevoke
            UserTokenService.deleteToken(target.id)
                .then(() => {
                    this.tokens = this.tokens.filter(t => t.id !== target.id)
                    if (this.expandedId === target.id) this.expandedId = null
                    NotificationService.$emit('NOTIFICATION', new Notification({ message: `Token "${target.description}" revoked.` }))
                })
                .catch(() => {})
                .finally(() => { this.pendingRevoke = null })
        },

        toggleLog (token) {
            if (this.expandedId === token.id) {
                this.expandedId = null
                this.accessLog = []
                return
            }
            this.expandedId = token.id
            this.accessLog = []
            this.logLoading = true
            UserTokenService.loadAccessLog(token.id)
                .then((log) => { this.accessLog = log })
                .catch(() => {})
                .finally(() => { this.logLoading = false })
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

.section-hint {
    font-size: 13px;
    font-weight: normal;
    color: #888;
    margin-left: 12px;
}

.token-pre {
    white-space: pre-wrap;
    word-wrap: break-word;
}

.log-row td,
.log-cell {
    background-color: #f9f9f9 !important;
    padding: 8px 16px !important;
}

.log-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
}

.log-table th {
    text-align: left;
    padding: 4px 12px 4px 0;
    color: #888;
    font-weight: 500;
    border-bottom: 1px solid #e0e0e0;
}

.log-table td {
    padding: 4px 12px 4px 0;
    border-bottom: 1px solid #f0f0f0;
}

.log-time {
    white-space: nowrap;
    color: #666;
}

.log-path {
    font-family: monospace;
    color: #444;
}

.log-loading,
.log-empty {
    color: #999;
    padding: 8px 0;
    font-size: 13px;
}

.expiry-soon {
    color: #e65100;
    font-weight: 500;
}

.expiry-expired {
    color: #c62828;
    font-weight: 500;
}
</style>
