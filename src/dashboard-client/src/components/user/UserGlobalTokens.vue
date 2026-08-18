<template>
    <div>
        <!-- ===== MCP Tokens ===== -->
        <md-card class="main-card">
            <md-card-header class="main-card-header fix-padding">
                <md-card-header-text>
                    <h3 class="md-title card-title">
                        <md-layout>
                            <md-layout md-vertical-align="center">MCP Tokens</md-layout>
                            <md-layout md-vertical-align="center">
                                <small class="section-hint">For use with the InfraBox MCP server (INFRABOX_MCP_TOKEN)</small>
                            </md-layout>
                        </md-layout>
                    </h3>
                </md-card-header-text>
            </md-card-header>

            <!-- Create form -->
            <md-card md-theme="white" class="clean-card">
                <md-card-area>
                    <md-list class="m-t-md m-b-md">
                        <md-list-item>
                            <md-input-container class="m-r-sm" style="flex: 2" :class="{'md-input-invalid': mcpNameError}">
                                <label>Token Name (e.g. "Claude Desktop")</label>
                                <md-input v-model="mcpForm.name" @keyup.enter.native="createMcpToken"></md-input>
                                <span class="md-error" v-if="mcpNameError">Name must be at least 3 characters</span>
                            </md-input-container>
                            <md-input-container class="m-r-sm" style="flex: 0 0 160px" :class="{'md-input-invalid': mcpDaysError}">
                                <label>Validity (days)</label>
                                <md-input v-model.number="mcpForm.expiresDays" type="number" min="1" max="365" placeholder="365"></md-input>
                                <span class="md-error" v-if="mcpDaysError">1–365 days</span>
                            </md-input-container>
                            <md-button class="md-icon-button md-list-action" @click="createMcpToken">
                                <md-icon md-theme="running" class="md-primary">add_circle</md-icon>
                                <md-tooltip>Create MCP token</md-tooltip>
                            </md-button>
                        </md-list-item>
                        <div v-if="userProjects.length > 0" style="padding: 0 16px 12px;">
                            <div style="font-size: 13px; color: #666; margin-bottom: 6px;">
                                Project scope
                                <small style="color: #999; margin-left: 6px;">leave all unchecked to allow access to all projects</small>
                            </div>
                            <div style="display: flex; flex-wrap: wrap; gap: 4px 16px;">
                                <label v-for="p in userProjects" :key="p.id" class="mcp-project-checkbox">
                                    <input type="checkbox" :value="p.id" v-model="mcpForm.selectedProjects">
                                    {{ p.name }}
                                </label>
                            </div>
                        </div>
                    </md-list>
                </md-card-area>
            </md-card>

            <!-- Token list -->
            <md-table-card class="clean-card">
                <md-table>
                    <md-table-header>
                        <md-table-row>
                            <md-table-head>Name</md-table-head>
                            <md-table-head>Projects</md-table-head>
                            <md-table-head>Created</md-table-head>
                            <md-table-head>Expires</md-table-head>
                            <md-table-head>Last Used</md-table-head>
                            <md-table-head>Trigger</md-table-head>
                            <md-table-head>Actions</md-table-head>
                        </md-table-row>
                    </md-table-header>
                    <md-table-body>
                        <template v-for="t in mcpTokens">
                            <md-table-row :key="t.token_id">
                                <md-table-cell>{{ t.name }}</md-table-cell>
                                <md-table-cell>
                                    <span v-if="!t.enabled_projects || Object.keys(t.enabled_projects).length === 0" class="mcp-all-projects">all projects</span>
                                    <span v-else class="mcp-project-count">{{ Object.keys(t.enabled_projects).length }} project(s)</span>
                                </md-table-cell>
                                <md-table-cell>{{ formatDate(t.created_at) }}</md-table-cell>
                                <md-table-cell>
                                    <span :class="expiryClass(t.expires_at)">
                                        {{ formatDate(t.expires_at) }}
                                        <md-icon v-if="isExpiringSoon(t.expires_at)" style="font-size:16px;vertical-align:middle">warning</md-icon>
                                    </span>
                                </md-table-cell>
                                <md-table-cell>{{ t.last_used_at ? formatDate(t.last_used_at) : '—' }}</md-table-cell>
                                <md-table-cell>
                                    <md-switch v-model="t.allow_trigger" @change="toggleMcpTrigger(t, $event)" class="mcp-trigger-switch"></md-switch>
                                </md-table-cell>
                                <md-table-cell>
                                    <md-button class="md-icon-button" @click="toggleScopeEdit(t)">
                                        <md-icon>edit</md-icon>
                                        <md-tooltip>Edit project scope</md-tooltip>
                                    </md-button>
                                    <md-button class="md-icon-button" @click="confirmMcpRevoke(t)">
                                        <md-icon class="md-primary">delete</md-icon>
                                        <md-tooltip>Revoke token</md-tooltip>
                                    </md-button>
                                </md-table-cell>
                            </md-table-row>

                            <!-- Inline scope editor -->
                            <md-table-row v-if="scopeEditId === t.token_id" :key="t.token_id + '-scope'" class="log-row">
                                <md-table-cell colspan="7" class="log-cell">
                                    <div style="padding: 8px 0;">
                                        <div style="font-size: 13px; color: #666; margin-bottom: 8px;">
                                            Project scope
                                            <small style="color: #999; margin-left: 6px;">leave all unchecked to allow access to all projects</small>
                                        </div>
                                        <div style="display: flex; flex-wrap: wrap; gap: 4px 16px; margin-bottom: 12px;">
                                            <label v-for="p in userProjects" :key="p.id" class="mcp-project-checkbox">
                                                <input type="checkbox" :value="p.id" v-model="scopeEditSelection">
                                                {{ p.name }}
                                            </label>
                                        </div>
                                        <button class="scope-btn scope-btn-primary" @click="saveScopeEdit(t)">Save</button>
                                        <button class="scope-btn" @click="scopeEditId = null">Cancel</button>
                                    </div>
                                </md-table-cell>
                            </md-table-row>
                        </template>

                        <md-table-row v-if="mcpTokens.length === 0">
                            <md-table-cell colspan="7">No MCP tokens yet. Create one above.</md-table-cell>
                        </md-table-row>
                    </md-table-body>
                </md-table>
            </md-table-card>
        </md-card>

        <!-- ===== Global Viewer Tokens ===== -->
        <md-card class="main-card" style="margin-top: 16px">
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
                                <small class="section-hint">Create and manage project tokens (INFRABOX_CLI_TOKEN)</small>
                            </md-layout>
                        </md-layout>
                    </h3>
                </md-card-header-text>
            </md-card-header>

            <!-- Create form -->
            <md-card md-theme="white" class="clean-card">
                <md-card-area>
                    <md-list class="m-t-md m-b-md">
                        <md-list-item v-if="adminProjects.length > 0">
                            <md-input-container class="m-r-sm" style="flex: 0 0 220px">
                                <label>Project</label>
                                <md-select v-model="projectTokenForm.projectId" name="project_token_select" id="project_token_select">
                                    <md-option v-for="p in adminProjects" :key="p.id" :value="p.id" class="bg-white">{{ p.name }}</md-option>
                                </md-select>
                            </md-input-container>
                            <md-input-container class="m-r-sm" style="flex: 2">
                                <label>Token Description (e.g. "Jenkins Integration")</label>
                                <md-input v-model="projectTokenForm.description" @keyup.enter.native="createProjectToken"></md-input>
                            </md-input-container>
                            <md-button :disabled="disableProjectTokenAdd" class="md-icon-button md-list-action" @click="createProjectToken">
                                <md-icon md-theme="running" class="md-primary">add_circle</md-icon>
                                <md-tooltip>Create project token</md-tooltip>
                            </md-button>
                        </md-list-item>
                        <div v-if="adminProjects.length === 0" style="padding: 0 16px 12px; font-size: 13px; color: #999;">
                            You have no projects with admin rights to create tokens for.
                        </div>
                    </md-list>
                </md-card-area>
            </md-card>

            <md-table-card class="clean-card">
                <md-table>
                    <md-table-header>
                        <md-table-row>
                            <md-table-head>Project</md-table-head>
                            <md-table-head>Description</md-table-head>
                            <md-table-head class="scope-col">Read</md-table-head>
                            <md-table-head class="scope-col">Write</md-table-head>
                            <md-table-head class="scope-col">Actions</md-table-head>
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
                                <md-table-cell class="scope-col">
                                    <md-icon v-if="token.scope_pull" class="md-primary">check</md-icon>
                                    <md-icon v-else>close</md-icon>
                                </md-table-cell>
                                <md-table-cell class="scope-col">
                                    <md-icon v-if="token.scope_push" class="md-primary">check</md-icon>
                                    <md-icon v-else>close</md-icon>
                                </md-table-cell>
                                <md-table-cell class="scope-col">
                                    <md-button class="md-icon-button" @click="confirmProjectTokenRevoke(project, token)">
                                        <md-icon class="md-primary">delete</md-icon>
                                        <md-tooltip>Delete token</md-tooltip>
                                    </md-button>
                                </md-table-cell>
                            </md-table-row>
                        </template>

                        <md-table-row v-if="projectTokensLoading">
                            <md-table-cell colspan="5">Loading...</md-table-cell>
                        </md-table-row>
                        <md-table-row v-else-if="totalProjectTokenCount === 0">
                            <md-table-cell colspan="5">No project tokens found.</md-table-cell>
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

        <!-- MCP new token dialog -->
        <md-dialog ref="mcpTokenDialog">
            <md-dialog-title>MCP Token Created</md-dialog-title>
            <md-dialog-content>
                Save this token somewhere safe — it will not be shown again.<br><br>
                <pre class="token-pre">{{ newMcpToken }}</pre><br>
                Use it with the InfraBox MCP server:<br>
                <pre>$ export INFRABOX_MCP_TOKEN=&lt;TOKEN_VALUE&gt;</pre>
            </md-dialog-content>
            <md-dialog-actions>
                <md-button class="md-primary" @click="closeMcpTokenDialog">OK</md-button>
            </md-dialog-actions>
        </md-dialog>

        <!-- MCP revoke confirmation dialog -->
        <md-dialog-confirm
            ref="mcpRevokeDialog"
            md-title="Revoke MCP Token"
            :md-content="`Revoke &quot;${pendingMcpRevoke ? pendingMcpRevoke.name : ''}&quot;? This cannot be undone.`"
            md-ok-text="Revoke"
            md-cancel-text="Cancel"
            @close="onMcpRevokeClose">
        </md-dialog-confirm>

        <!-- Project token revoke confirmation dialog -->
        <md-dialog-confirm
            ref="projectTokenRevokeDialog"
            md-title="Delete Project Token"
            :md-content="`Delete &quot;${pendingProjectTokenRevoke ? pendingProjectTokenRevoke.token.description : ''}&quot;? This cannot be undone.`"
            md-ok-text="Delete"
            md-cancel-text="Cancel"
            @close="onProjectTokenRevokeClose">
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
        loadedProjectIds: [],
        pendingProjectTokenRevoke: null,
        form: {
            description: '',
            expiresDays: 365
        },
        projectTokenForm: {
            projectId: '',
            description: ''
        },
        mcpTokens: [],
        newMcpToken: '',
        pendingMcpRevoke: null,
        scopeEditId: null,
        scopeEditSelection: [],
        mcpForm: {
            name: '',
            expiresDays: 365,
            selectedProjects: []
        }
    }),

    computed: {
        disableAdd () {
            return !this.form.description || this.form.description.length < 3 ||
                !this.form.expiresDays || this.form.expiresDays < 1 || this.form.expiresDays > 3650
        },
        disableProjectTokenAdd () {
            return !this.projectTokenForm.projectId ||
                !this.projectTokenForm.description || this.projectTokenForm.description.length < 3
        },
        disableMcpAdd () {
            return !this.mcpForm.name || this.mcpForm.name.length < 3 ||
                !this.mcpForm.expiresDays || this.mcpForm.expiresDays < 1 || this.mcpForm.expiresDays > 365
        },
        mcpNameError () {
            return this.mcpForm.name !== '' && this.mcpForm.name.length < 3
        },
        mcpDaysError () {
            return this.mcpForm.expiresDays !== '' && this.mcpForm.expiresDays !== null &&
                (this.mcpForm.expiresDays < 1 || this.mcpForm.expiresDays > 365)
        },
        userProjects () {
            // Only projects the user is a collaborator on. Opening a public/other
            // project by URL injects it into store.state.projects without a
            // collaborator role (userrole is undefined), and MCP tokens are only
            // usable on projects the user is a member of — so exclude those here to
            // avoid offering a scope the resulting token can't actually access.
            return (this.$store.state.projects || []).filter(p => p.userrole)
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

        UserTokenService.loadMcpTokens().then((tokens) => {
            this.mcpTokens = tokens
        }).catch(() => {})

        this.loadProjectTokens()
    },

    watch: {
        // store.state.projects is populated asynchronously and can grow across
        // multiple commits (e.g. a single-project load followed by the full list).
        // Re-run the loader whenever the admin project set grows; loadProjectTokens()
        // only fetches projects it hasn't fetched yet, so late arrivals are picked up.
        'adminProjects.length' () {
            this.loadProjectTokens()
        }
    },

    methods: {
        loadProjectTokens () {
            // Only fetch projects we haven't fetched yet (tracked by id), so admin
            // projects arriving in a later store commit still get loaded. Use
            // _reloadTokens() (returns a real Promise) instead of _loadTokens() so
            // the loading flag stays on until the GETs actually complete and the
            // data is fresh on every visit.
            const pending = this.adminProjects.filter(p => this.loadedProjectIds.indexOf(p.id) === -1)
            if (pending.length === 0) return
            pending.forEach(p => this.loadedProjectIds.push(p.id))
            this.projectTokensLoading = true
            Promise.all(pending.map(p => p._reloadTokens()))
                .catch(() => {})
                .finally(() => { this.projectTokensLoading = false })
        },

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

        createProjectToken () {
            if (this.disableProjectTokenAdd) return
            const project = this.adminProjects.find(p => p.id === this.projectTokenForm.projectId)
            if (!project) return
            // Reuse the same Project.addToken() used by project settings — it posts to
            // POST projects/{id}/tokens and reloads that project's token list on success.
            project.addToken(this.projectTokenForm.description)
                .then((token) => {
                    if (!token) return
                    this.newToken = token
                    this.$refs['tokenDialog'].open()
                    this.projectTokenForm.description = ''
                })
        },

        confirmProjectTokenRevoke (project, token) {
            this.pendingProjectTokenRevoke = { project, token }
            this.$refs['projectTokenRevokeDialog'].open()
        },

        onProjectTokenRevokeClose (type) {
            if (type !== 'ok' || !this.pendingProjectTokenRevoke) {
                this.pendingProjectTokenRevoke = null
                return
            }
            const { project, token } = this.pendingProjectTokenRevoke
            // Reuse the same Project.deleteToken() used by project settings — it
            // DELETEs projects/{id}/tokens/{tid} and reloads that project's token
            // list on success.
            project.deleteToken(token.id)
                .finally(() => { this.pendingProjectTokenRevoke = null })
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
        },

        createMcpToken () {
            if (!this.mcpForm.name || this.mcpForm.name.length < 3) {
                NotificationService.$emit('NOTIFICATION', new Notification({ message: 'Token name must be at least 3 characters.' }))
                return
            }
            const days = this.mcpForm.expiresDays
            if (!days || days < 1 || days > 365) {
                NotificationService.$emit('NOTIFICATION', new Notification({ message: 'Validity must be between 1 and 365 days.' }))
                return
            }
            const enabledProjects = this.mcpForm.selectedProjects.length > 0
                ? this.mcpForm.selectedProjects.reduce((acc, id) => { acc[id] = null; return acc }, {})
                : {}
            UserTokenService.createMcpToken(this.mcpForm.name, enabledProjects, this.mcpForm.expiresDays)
                .then((result) => {
                    this.mcpTokens.unshift({
                        token_id: result.token_id,
                        name: result.name,
                        enabled_projects: result.enabled_projects,
                        allow_trigger: result.allow_trigger,
                        expires_at: result.expires_at,
                        created_at: new Date().toISOString(),
                        last_used_at: null
                    })
                    this.newMcpToken = result.token
                    this.$refs['mcpTokenDialog'].open()
                    this.mcpForm.name = ''
                    this.mcpForm.expiresDays = 365
                    this.mcpForm.selectedProjects = []
                })
                .catch(() => {})
        },

        confirmMcpRevoke (token) {
            this.pendingMcpRevoke = token
            this.$refs['mcpRevokeDialog'].open()
        },

        onMcpRevokeClose (type) {
            if (type !== 'ok' || !this.pendingMcpRevoke) {
                this.pendingMcpRevoke = null
                return
            }
            const target = this.pendingMcpRevoke
            UserTokenService.revokeMcpToken(target.token_id)
                .then(() => {
                    this.mcpTokens = this.mcpTokens.filter(t => t.token_id !== target.token_id)
                    NotificationService.$emit('NOTIFICATION', new Notification({ message: `MCP token "${target.name}" revoked.` }))
                })
                .catch(() => {})
                .finally(() => { this.pendingMcpRevoke = null })
        },

        toggleScopeEdit (token) {
            if (this.scopeEditId === token.token_id) {
                this.scopeEditId = null
                return
            }
            this.scopeEditId = token.token_id
            this.scopeEditSelection = Object.keys(token.enabled_projects || {})
        },

        saveScopeEdit (token) {
            const enabledProjects = this.scopeEditSelection.reduce((acc, id) => {
                acc[id] = null
                return acc
            }, {})
            UserTokenService.updateMcpToken(token.token_id, enabledProjects)
                .then(() => {
                    token.enabled_projects = enabledProjects
                    this.scopeEditId = null
                    NotificationService.$emit('NOTIFICATION', new Notification({ message: `Scope updated for "${token.name}".` }))
                })
                .catch(() => {})
        },

        toggleMcpTrigger (token, newVal) {
            // md-switch emits the new model value via @change. Rely on that
            // explicit value rather than reading token.allow_trigger, which is
            // not guaranteed to be updated by v-model yet when @change fires
            // (that timing gap caused the "first click is a no-op" bug).
            token.allow_trigger = newVal
            UserTokenService.setMcpTrigger(token.token_id, newVal)
                .catch(() => { token.allow_trigger = !newVal })
        },

        closeMcpTokenDialog () {
            this.$refs['mcpTokenDialog'].close()
            this.newMcpToken = ''
        }
    }
}
</script>

<style scoped>
/* Center the Read/Write/Actions columns. vue-material left-aligns header text
   while cell icons/buttons sit centered-ish in their container, so the two
   never line up by default. Center both the header container and the cell
   container (verified: header-text center and icon center then coincide). */
.scope-col >>> .md-table-head-container {
    display: flex;
    justify-content: center;
}
.scope-col >>> .md-table-head-text {
    padding-left: 0;
    padding-right: 0;
}
/* Cells containing a button get vue-material's .md-has-action rule
   (justify-content: space-between), so override it with !important to keep
   the Actions button centered like the Read/Write icons. */
.scope-col >>> .md-table-cell-container {
    display: flex;
    justify-content: center !important;
    padding-left: 0;
    padding-right: 0;
}
/* vue-material gives the last icon-button a negative right margin
   (margin: 0 -10px 0 0) which throws off the centering; reset it. */
.scope-col >>> .md-button {
    margin: 0;
}

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
    overflow: visible !important;
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

.mcp-all-projects {
    color: #888;
    font-style: italic;
    font-size: 13px;
}

.mcp-project-count {
    font-size: 13px;
}

.mcp-trigger-switch {
    margin: 0;
}

.mcp-project-checkbox {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 13px;
    cursor: pointer;
    user-select: none;
    color: #444;
}

.mcp-project-checkbox input {
    cursor: pointer;
}

.scope-btn {
    display: inline-block;
    margin-top: 8px;
    margin-right: 8px;
    padding: 6px 16px;
    border: none;
    border-radius: 2px;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    text-transform: uppercase;
    background: #e0e0e0;
    color: #212121;
}

.scope-btn:hover {
    background: rgba(0,0,0,0.07);
}

.scope-btn-primary {
    background: #009688;
    color: #fff;
}

.scope-btn-primary:hover {
    background: #00796b;
}
</style>
