<template>
    <div class="m-sm full-height">
        <md-card md-theme="white" class="full-height clean-card">
            <md-card-header>
                <md-card-header-text class="setting-list">
                    <md-icon>security</md-icon>
                    <span>SSHKeys</span>
                </md-card-header-text>
            </md-card-header>
            <md-card-area>
                    <md-list class="m-t-md m-b-md md-double-line">
                        <md-list-item>
                            <div class="md-list-text-container">
                                <span>
                                    <md-input-container>
                                        <label>Name</label>
                                        <md-input @keyup.enter.native="addSSHKey" required v-model="name"></md-input>
                                    </md-input-container>
                                </span>
                            </div>

                            <div class="md-list-text-container">
                                <span>
                                    <md-input-container>
                                        <label for="secret_select">Secret</label>
                                        <md-select name="secret_select" id="secret_select" v-model="secret">
                                            <md-option v-for="s in project.secrets" :value="s.name" :key="s.name" class="bg-white">{{s.name}}</md-option>
                                        </md-select>
                                    </md-input-container>
                                </span>
                            </div>

                            <md-button class="md-icon-button md-list-action" @click="addSSHKey()">
                                <md-icon md-theme="running" class="md-primary">add_circle</md-icon>
                                <md-tooltip>Add SSH Key</md-tooltip>
                            </md-button>
                        </md-list-item>
                        <md-list-item v-for="k in project.sshkeys" :key="k.id">
                            <div class="md-input-container m-r-xl md-theme-white">
                                {{ k.name }}
                            </div>
                            <div class="md-input-container m-r-xl md-theme-white">
                                {{ k.secret }}
                            </div>
                            <md-button class="md-icon-button md-list-action" @click="deleteSSHKey(k.id)">
                                <md-icon class="md-primary">delete</md-icon>
                                <md-tooltip>Remove sshkey</md-tooltip>
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
    data: () => {
        return {
            'name': '',
            'secret': ''
        }
    },
    created () {
        this.project._loadSSHKeys()
    },
    methods: {
        deleteSSHKey (id) {
            NewAPIService.delete(`projects/${this.project.id}/sshkeys/${id}`)
                .then((response) => {
                    NotificationService.$emit('NOTIFICATION', new Notification(response))
                    this.project._reloadSSHKeys()
                })
                .catch((err) => {
                    NotificationService.$emit('NOTIFICATION', new Notification(err))
                })
        },
        addSSHKey () {
            const d = {
                name: this.name,
                secret: this.secret
            }
            NewAPIService.post(`projects/${this.project.id}/sshkeys`, d)
                .then((response) => {
                    NotificationService.$emit('NOTIFICATION', new Notification(response))
                    this.name = ''
                    this.secret = ''
                    this.project._reloadSSHKeys()
                })
                .catch((err) => {
                    NotificationService.$emit('NOTIFICATION', new Notification(err))
                })
        }
    }
}
</script>
