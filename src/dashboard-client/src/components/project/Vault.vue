<template>
    <div class="m-sm full-height">
        <md-card md-theme="white" class="full-height clean-card">
            <md-card-header>
                <md-card-header-text class="setting-list">
                    <md-icon>security</md-icon>
                    <span>Vault</span>
                </md-card-header-text>
            </md-card-header>
            <md-card-area>
                    <md-list class="m-t-md m-b-md">
                        <md-list-item>
                            <md-input-container class="m-l-sm">
                                <label>Name</label>
                                <md-textarea v-model="name" required></md-textarea>
                            </md-input-container>
                            <md-input-container class="m-l-sm">
                              <label>Url</label>
                              <md-textarea v-model="url" required></md-textarea>
                            </md-input-container>
                            <md-input-container class="m-l-sm">
                                <label>Namespace</label>
                                <md-textarea v-model="namespace"></md-textarea>
                            </md-input-container>
                            <md-input-container>
                                <label>Version</label>
                                <md-select name="version" id="version" v-model="version" required>
                                    <md-option value="v1" class="bg-white">1</md-option>
                                    <md-option value="v2" class="bg-white">2</md-option>
                                </md-select>
                            </md-input-container>
                            <md-input-container class="m-l-sm">
                              <label>Token</label>
                              <md-textarea v-model="token"></md-textarea>
                            </md-input-container>
                            <md-input-container class="m-l-sm">
                                <label>CA</label>
                                <md-textarea v-model="ca"></md-textarea>
                            </md-input-container>
                            <md-input-container class="m-l-sm">
                                <label>RoleId</label>
                                <md-textarea v-model="role_id"></md-textarea>
                            </md-input-container>
                            <md-input-container class="m-l-sm">
                                <label>SecretId</label>
                                <md-textarea v-model="secret_id"></md-textarea>
                            </md-input-container>
                            <md-button class="md-icon-button md-list-action" @click="addVault()">
                                <md-icon md-theme="running" class="md-primary">add_circle</md-icon>
                                <md-tooltip>Add new Vault record</md-tooltip>
                            </md-button>
                        </md-list-item>
                        <md-list-item v-for="v in project.vault" :key="v.id">
                            <div class="md-input-container m-r-xl md-theme-white">
                                {{ v.name }}
                            </div>
                            <md-button type="submit" class="md-icon-button md-list-action" @click="deleteVault(v.id)">
                                <md-icon class="md-primary">delete</md-icon>
                                <md-tooltip>Delete secret permanently</md-tooltip>
                            </md-button>
                        </md-list-item>
                    </md-list>
            </md-card-area>
        </md-card>
    </div>
</template>

<script>
import NewAPIService from '../../services/NewAPIService'
import NotificationService from '../../services/NotificationService'
import Notification from '../../models/Notification'

export default {
    props: ['project'],
    data: () => ({
        name: '',
        url: '',
        namespace: '',
        version: '',
        token: '',
        ca: '',
        role_id: '',
        secret_id: ''
    }),
    created () {
        this.project._loadVault()
    },
    methods: {
        deleteVault (id) {
            NewAPIService.delete(`projects/${this.project.id}/vault/${id}`)
                .then((response) => {
                    NotificationService.$emit('NOTIFICATION', new Notification(response))
                    this.project._reloadVault()
                })
                .catch((err) => {
                    NotificationService.$emit('NOTIFICATION', new Notification(err))
                })
        },
        addVault () {
            const d = { name: this.name, url: this.url, namespace: this.namespace, version: this.version, token: this.token, ca: this.ca, role_id: this.role_id, secret_id: this.secret_id }
            NewAPIService.post(`projects/${this.project.id}/vault`, d)
                .then((response) => {
                    NotificationService.$emit('NOTIFICATION', new Notification(response))
                    this.name = ''
                    this.url = ''
                    this.namespace = ''
                    this.version = ''
                    this.token = ''
                    this.ca = ''
                    this.role_id = ''
                    this.secret_id = ''
                    this.project._reloadVault()
                })
                .catch((err) => {
                    NotificationService.$emit('NOTIFICATION', new Notification(err))
                })
        }
    }
}
</script>
