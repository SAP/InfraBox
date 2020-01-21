<template>
<div class="m-sm full-height">
    <md-card md-theme="white" class="full-height clean-card">
        <md-card-header>
            <md-card-header-text class="setting-list">
                <md-icon>bookmark</md-icon>
                <span>Visibility</span>
            </md-card-header-text>
        </md-card-header>
        <md-card-area>
            <md-button v-if="project.public" @click="makePrivate">
                <i class="fa fa-fw fa-user"></i><span> Make Private</span>
            </md-button>

            <md-button v-if="!project.public" @click="makePublic">
                <i class="fa fa-fw fa-users"></i><span> Make Public</span>
            </md-button>
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
    methods: {
        makePublic () {
            console.log(this.project)
            NewAPIService.post(`projects/${this.project.id}/visibility/`, {private: false})
                .then((response) => {
                    NotificationService.$emit('NOTIFICATION', new Notification(response))
                    this.project.public = true
                })
                .catch((err) => {
                    NotificationService.$emit('NOTIFICATION', new Notification(err))
                })
        },
        makePrivate () {
            NewAPIService.post(`projects/${this.project.id}/visibility/`, {private: true})
                .then((response) => {
                    NotificationService.$emit('NOTIFICATION', new Notification(response))
                    this.project.public = false
                })
                .catch((err) => {
                    NotificationService.$emit('NOTIFICATION', new Notification(err))
                })
        }
    }
}
</script>