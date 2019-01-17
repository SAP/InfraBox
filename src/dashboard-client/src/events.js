import Vue from 'vue'
import VueSocketio from 'vue-socket.io'
import Socket from 'socket.io-client'

let protocol = 'ws:'
if (window.location.protocol === 'https:') {
    protocol = 'wss:'
}

const host = protocol + '//' + process.env.DASHBOARD_HOST

const socket = Socket(host, {
    path: '/api/v1/socket.io'
})

socket.on('connect_error', (error) => {
    console.log(error)
    socket.close()
})

Vue.use(VueSocketio, socket)

export default new Vue({
    sockets: {
        connect () {
            this.$emit('CONNECTED')
        },
        disconnect () {
            this.$emit('DISCONNECTED')
        },
        'notify:job' (val) {
            this.$emit('NOTIFY_JOBS', val)
        },
        'notify:console' (val) {
            this.$emit('NOTIFY_CONSOLE', val)
        }
    },
    methods: {
        listenJobs (project) {
            this.$socket.emit('listen:jobs', project.id)
        },
        listenConsole (id) {
            this.$socket.emit('listen:dashboard-console', id)
        }
    }
})
