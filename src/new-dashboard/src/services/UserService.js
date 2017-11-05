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

    _loadSettings () {
        return APIService.get(`settings`)
            .then((s) => {
                store.commit('setSettings', s)
            })
    }

    _loadUser () {
        return APIService.get(`user`)
            .then((d) => {
                const u = new User(d.username,
                                   d.avatar_url,
                                   d.name,
                                   d.email,
                                   d.github_id)
                store.commit('setUser', u)

                if (u.hasGithubAccount() && store.state.settings.INFRABOX_GITHUB_ENABLED) {
                    return APIService.get('github/repos')
                }
            })
            .then((d) => {
                if (d) {
                    console.log(d)
                    store.commit('setGithubRepos', d)
                }
                ProjectService.init()
            })
    }
}

export default new UserService()
