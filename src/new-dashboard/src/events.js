import Vue from 'vue'
import VueSocketio from 'vue-socket.io'
import Socket from 'socket.io-client'

let protocol = 'ws:'
if (window.location.protocol === 'https:') {
    protocol = 'wss:'
}

const host = protocol + '//' + process.env.DASHBOARD_HOST

const socket = Socket(host, {
    path: '/live/dashboard/'
})

Vue.use(VueSocketio, socket)

function getCookie (cname) {
    const name = cname + '='
    const ca = document.cookie.split(';')

    for (let c of ca) {
        while (c.charAt(0) === ' ') {
            c = c.substring(1)
        }

        if (c.indexOf(name) === 0) {
            return c.substring(name.length, c.length)
        }
    }
    return ''
}

export function getToken () {
    return getCookie('token')
}

export default new Vue({
    sockets: {
        connect () {
            this.$socket.emit('auth', getToken())
        },
        'notify:jobs' (val) {
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
            this.$socket.emit('listen:console', id)
        }
    }
})
