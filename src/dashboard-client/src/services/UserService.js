import store from '../store'
import NewAPIService from './NewAPIService'
import ProjectService from './ProjectService'
import User from '../models/User'

class UserService {
    init () {
        this._loadSettings().then(() => {
            return this._loadUser()
        })
    }

    login () {
        this.init()
    }

    _getCookie (cname) {
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

        return null
    }

    getToken () {
        return this._getCookie('token')
    }

    isLoggedIn () {
        return this.getToken() !== null
    }

    logout () {
        document.cookie = 'token=; expires=Thu, 01 Jan 1970 00:00:01 GMT; path=/; Max-Age=0'
        store.commit('setUser', null)
    }

    _loadSettings () {
        return NewAPIService.get(`settings/`)
            .then((s) => {
                console.log(s)
                store.commit('setSettings', s)
            })
    }

    _loadUser () {
        return NewAPIService.get(`user/`, true)
            .then((d) => {
                const u = new User(
                    d.username,
                    d.avatar_url,
                    d.name,
                    d.email,
                    d.github_id,
                    d.id,
                    d.role)
                store.commit('setUser', u)
                ProjectService.init()
            })
            .catch(() => {
                // ignore
            })
    }

    loadRepos () {
        if (store.state.user.hasGithubAccount() && store.state.settings.INFRABOX_GITHUB_ENABLED) {
            return NewAPIService.get('github/repos/')
                .then((d) => {
                    if (d) {
                        store.commit('setGithubRepos', d)
                    }
                })
        }
    }
}

export default new UserService()
