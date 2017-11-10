<template>
    <md-snackbar :md-position="vertical + ' ' + horizontal" ref="snackbar" :md-duration="duration">
        <md-icon>{{ icon }} </md-icon>
        <span>{{ message }}</span>
        <md-button class="md-accent" md-theme="running" @click="$refs.snackbar.close()">Close</md-button>
    </md-snackbar>
</template>

<script>
import NotificationService from '../services/NotificationService'
export default {
    data: () => ({
        vertical: 'top',
        horizontal: 'center',
        duration: 4000,
        message: '',
        icon: ''
    }),
    created () {
        const self = this
        NotificationService.$on('NOTIFICATION', function (n) {
            self.$refs.snackbar.close()
            self.message = n.message
            self.icon = n.icon
            self.$refs.snackbar.open()
        })
    }
}
</script>
