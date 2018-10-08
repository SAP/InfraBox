import Vue from 'vue'

import router from '../router'

class NewAPIService {
    constructor () {
        this.api = process.env.NEW_API_PATH
    }

    _handleError (ignoreUnauthorized) {
        return (err) => {
            if (err.status === 401 && !ignoreUnauthorized) {
                router.push('/login')
            }

            throw err
        }
    }

    get (url, ignoreUnauthorized) {
        const u = this.api + url
        console.log(`GET API: ${url}`)
        return Vue.http.get(u)
            .then((response) => {
                return response.body
            })
            .catch(this._handleError(ignoreUnauthorized))
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
            .catch(this._handleError(false))
    }

    post (url, payload) {
        console.log(`POST API: ${url}`)
        const u = this.api + url
        return Vue.http.post(u, payload)
            .then((response) => {
                return response.body
            })
            .catch(this._handleError(false))
    }

    put (url, payload) {
        console.log(`PUT API: ${url}`)
        const u = this.api + url
        return Vue.http.put(u, payload)
            .then((response) => {
                return response.body
            })
            .catch(this._handleError(false))
    }
}

export default new NewAPIService()
