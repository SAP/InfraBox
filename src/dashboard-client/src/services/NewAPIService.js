import Vue from 'vue'

import NotificationService from '../services/NotificationService'
import Notification from '../models/Notification'
import router from '../router'

class NewAPIService {
    constructor () {
        this.api = process.env.NEW_API_PATH
    }

    get (url) {
        const u = this.api + url
        console.log(`GET API: ${url}`)
        return Vue.http.get(u)
            .then((response) => {
                return response.body
            })
            .catch((err) => {
                if (err.status !== 401) {
                    NotificationService.$emit('NOTIFICATION', new Notification(err))
                }

                throw err
            })
    }

    openAPIUrl (u) {
        const url = this.api + u
        window.open(url, '_blank')
    }

    delete (url) {
        const u = this.api + url
        console.log(`DELETE API: ${url}`)
        return Vue.http.delete(u)
            .then((response) => {
                return response.body
            })
            .catch((err) => {
                if (err.status === 401) {
                    router.push('/login')
                } else {
                    NotificationService.$emit('NOTIFICATION', new Notification(err))
                }

                throw err
            })
    }

    post (url, payload) {
        console.log(`POST API: ${url}`)
        const u = this.api + url
        return Vue.http.post(u, payload)
            .then((response) => {
                return response.body
            })
            .catch((err) => {
                if (err.status === 401) {
                    router.push('/login')
                } else {
                    NotificationService.$emit('NOTIFICATION', new Notification(err))
                }

                throw err
            })
    }
}

export default new NewAPIService()
