import Vue from 'vue'

class APIService {
    constructor () {
        this.host = 'http://localhost:3000'
    }

    get (url) {
        const u = this.host + url
        return Vue.http.get(u)
            .then((response) => {
                return response.body
            })
    }
}

export default new APIService()
