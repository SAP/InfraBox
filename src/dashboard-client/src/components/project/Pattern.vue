<template>
    <div class="m-sm full-height">
        <md-card md-theme="white" class="full-height clean-card">
            <md-card-header>
                <md-card-header-text class="setting-list">
                    <md-icon>security</md-icon>
                    <span>Build Skip Pattern</span>
                </md-card-header-text>
            </md-card-header>
            <md-card-area>
                    <md-list class="m-t-md m-b-md">
                        <md-list-item>
                            <md-input-container class="m-l-sm">
                                <label>Infrabox Build will be skipped if Github event ref matched the pattern</label>
                                <md-textarea v-model="skip_pattern" required></md-textarea>
                            </md-input-container>
                            <md-button class="md-icon-button md-list-action" @click="addPattern()">
                                <md-icon md-theme="running" class="md-primary">add_circle</md-icon>
                                <md-tooltip>Using regex to add new pattern</md-tooltip>
                            </md-button>
                        </md-list-item>
                        <md-list-item v-for="v in project.pattern" :key="v.id">
                            <div class="md-input-container m-r-xl md-theme-white">
                                {{ v.skip_pattern }}
                            </div>
                            <md-button type="submit" class="md-icon-button md-list-action" @click="deletePattern()">
                                <md-icon class="md-primary">delete</md-icon>
                                <md-tooltip>Delete pattern permanently</md-tooltip>
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
        skip_pattern: ''
    }),
    created () {
        this.project._loadPattern()
    },
    methods: {
        deletePattern () {
            NewAPIService.delete(`projects/${this.project.id}/pattern`)
                .then((response) => {
                    NotificationService.$emit('NOTIFICATION', new Notification(response))
                    this.project._reloadPattern()
                })
                .catch((err) => {
                    NotificationService.$emit('NOTIFICATION', new Notification(err))
                })
        },
        addPattern () {
            const d = { skip_pattern: this.skip_pattern }
            NewAPIService.post(`projects/${this.project.id}/pattern`, d)
                .then((response) => {
                    NotificationService.$emit('NOTIFICATION', new Notification(response))
                    this.skip_pattern = ''
                    this.project._reloadPattern()
                })
                .catch((err) => {
                    NotificationService.$emit('NOTIFICATION', new Notification(err))
                })
        }
    }
}
</script>
