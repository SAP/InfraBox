<template>
    <div class="m-sm full-height">
        <md-card md-theme="white" class="full-height clean-card">
            <md-card-header>
                <md-card-header-text class="setting-list">
                    <md-icon>security</md-icon>
                    <span>Secrets</span>
                </md-card-header-text>
            </md-card-header>
            <md-card-area>
                    <md-list class="m-t-md m-b-md">
                        <md-list-item>
                            <md-input-container class="m-r-sm">
                                <label>Secret Name</label>
                                <md-input v-model="name" required></md-input>
                            </md-input-container>
                            <md-input-container class="m-l-sm">
                                <label>Secret Value</label>
                                <md-textarea v-model="value" required></md-textarea>
                            </md-input-container>
                            <md-button class="md-icon-button md-list-action" @click="addSecret()">
                                <md-icon md-theme="running" class="md-primary">add_circle</md-icon>
                                <md-tooltip>Add new secret</md-tooltip>
                            </md-button>
                        </md-list-item>
                        <md-list-item v-for="secret in project.secrets" :key="secret.id">
                            <div class="md-input-container m-r-xl md-theme-white">
                                {{ secret.name }}
                            </div>
                            <md-button type="submit" class="md-icon-button md-list-action" @click="deleteSecret(secret.id)">
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
        value: ''
    }),
    created () {
        this.project._loadSecrets()
    },
    methods: {
        deleteSecret (id) {
            NewAPIService.delete(`projects/${this.project.id}/secrets/${id}`)
                .then((response) => {
                    NotificationService.$emit('NOTIFICATION', new Notification(response))
                    this.project._reloadSecrets()
                })
                .catch((err) => {
                    NotificationService.$emit('NOTIFICATION', new Notification(err))
                })
        },
        addSecret () {
            const d = { name: this.name, value: this.value }
            NewAPIService.post(`projects/${this.project.id}/secrets`, d)
                .then((response) => {
                    NotificationService.$emit('NOTIFICATION', new Notification(response))
                    this.name = ''
                    this.value = ''
                    this.project._reloadSecrets()
                })
                .catch((err) => {
                    NotificationService.$emit('NOTIFICATION', new Notification(err))
                })
        }
    }
}
</script>
