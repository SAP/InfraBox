<template>
    <md-dialog ref="disconnected-dialog">
      <md-dialog-title>Disconnected</md-dialog-title>

      <md-dialog-content>You have been disconnected from InfraBox.</md-dialog-content>

      <md-dialog-actions>
          <md-button class="md-primary" @click="reload()">reconnect</md-button>
      </md-dialog-actions>
    </md-dialog>
</template>

<script>
import events from '../../events'
import store from '../../store'

export default {
    created () {
        events.$on('DISCONNECTED', () => {
            if (store.state.user) {
                this.$refs['disconnected-dialog'].open()
            }
        })
    },
    methods: {
        reload () {
            window.location.reload(false)
        }
    }
}
</script>
