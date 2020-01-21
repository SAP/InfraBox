<template>
    <div class="m-sm full-height">
        <md-card md-theme="white" class="full-height clean-card">
            <md-card-header>
                <md-card-header-text class="setting-list">
                    <md-icon>security</md-icon>
                    <span>Cronjobs</span>
                </md-card-header-text>
            </md-card-header>
            <md-card-area>
                    <md-list class="m-t-md m-b-md">
                        <md-list-item>
                            <md-input-container class="m-r-sm">
                                <label>Cron Name</label>
                                <md-input v-model="name" required></md-input>
                            </md-input-container>
                            <md-input-container class="m-l-sm">
                                <label>Minute</label>
                                <md-input v-model="minute" required></md-input>
                            </md-input-container>
                            <md-input-container class="m-l-sm">
                                <label>Hour</label>
                                <md-input v-model="hour" required></md-input>
                            </md-input-container>
                            <md-input-container class="m-l-sm">
                                <label>Day of the month</label>
                                <md-input v-model="day_month" required></md-input>
                            </md-input-container>
                            <md-input-container class="m-l-sm">
                                <label>Month</label>
                                <md-input v-model="month" required></md-input>
                            </md-input-container>
                            <md-input-container class="m-l-sm">
                                <label>Day of the week</label>
                                <md-input v-model="day_week" required></md-input>
                            </md-input-container>
                            <md-input-container class="m-l-sm">
                                <label>sha</label>
                                <md-input v-model="sha" required></md-input>
                            </md-input-container>
                            <md-input-container class="m-l-sm">
                                <label>infrabox.json path</label>
                                <md-input v-model="infrabox_file" required></md-input>
                            </md-input-container>
                            <md-button class="md-icon-button md-list-action" @click="addCronJob()">
                                <md-icon md-theme="running" class="md-primary">add_circle</md-icon>
                                <md-tooltip>Add new Cron Job</md-tooltip>
                            </md-button>
                        </md-list-item>
                        <md-list-item v-for="cron in project.cronjobs" :key="cron.id">
                            <div class="md-input-container m-r-xl md-theme-white">
                                {{ cron.name }}
                            </div>
                            <div class="md-input-container m-r-xl md-theme-white">
                                {{ cron.minute }}
                            </div>
                            <div class="md-input-container m-r-xl md-theme-white">
                                {{ cron.hour }}
                            </div>
                            <div class="md-input-container m-r-xl md-theme-white">
                                {{ cron.day_month }}
                            </div>
                            <div class="md-input-container m-r-xl md-theme-white">
                                {{ cron.month }}
                            </div>
                            <div class="md-input-container m-r-xl md-theme-white">
                                {{ cron.day_week }}
                            </div>
                            <div class="md-input-container m-r-xl md-theme-white">
                                {{ cron.sha }}
                            </div>
                            <div class="md-input-container m-r-xl md-theme-white">
                                {{ cron.infrabox_file }}
                            </div>
                            <md-button type="submit" class="md-icon-button md-list-action" @click="deleteCronJob(cron.id)">
                                <md-icon class="md-primary">delete</md-icon>
                                <md-tooltip>Delete Cron Job permanently</md-tooltip>
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
        minute: '',
        hour: '',
        day_month: '',
        month: '',
        day_week: '',
        sha: '',
        infrabox_file: 'infrabox.json'
    }),
    created () {
        this.project._loadCronJobs()
    },
    methods: {
        deleteCronJob (id) {
            NewAPIService.delete(`projects/${this.project.id}/cronjobs/${id}`)
                .then((response) => {
                    NotificationService.$emit('NOTIFICATION', new Notification(response))
                    this.project._reloadCronJobs()
                })
                .catch((err) => {
                    NotificationService.$emit('NOTIFICATION', new Notification(err))
                })
        },
        addCronJob () {
            const d = {
                name: this.name,
                minute: this.minute,
                hour: this.hour,
                day_month: this.day_month,
                month: this.month,
                day_week: this.day_week,
                sha: this.sha,
                infrabox_file: this.infrabox_file
            }
            NewAPIService.post(`projects/${this.project.id}/cronjobs`, d)
                .then((response) => {
                    NotificationService.$emit('NOTIFICATION', new Notification(response))
                    this.name = ''
                    this.minute = ''
                    this.hour = ''
                    this.day_month = ''
                    this.month = ''
                    this.day_week = ''
                    this.sha = ''
                    this.infrabox_file = 'infrabox.json'
                    this.project._reloadCronJobs()
                })
                .catch((err) => {
                    NotificationService.$emit('NOTIFICATION', new Notification(err))
                })
        }
    }
}
</script>
