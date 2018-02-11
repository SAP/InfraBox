import store from '../store'
import APIService from './APIService'
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

    _loadSettings () {
        return APIService.get(`settings/`)
            .then((s) => {
                console.log(s)
                store.commit('setSettings', s)
            })
    }

    _loadUser () {
        return APIService.get(`user/`, true)
            .then((d) => {
                const u = new User(d.username,
                                   d.avatar_url,
                                   d.name,
                                   d.email,
                                   d.github_id)
                store.commit('setUser', u)

                if (u.hasGithubAccount() && store.state.settings.INFRABOX_GITHUB_ENABLED) {
                    return APIService.get('github/repos/')
                }
            })
            .then((d) => {
                if (d) {
                    store.commit('setGithubRepos', d)
                }
                ProjectService.init()
            })
            .catch(() => {
                // ignore
            })
    }
}

export default new UserService()
