import store from '../store'
import APIService from '../services/APIService'
import User from '../models/User'

class UserService {
    init () {
        this._loadUser()
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

                console.log(u)
                if (u.hasGithubAccount()) {
                    console.log('Load repos')
                    return APIService.get('github/repos')
                }
            })
            .then((d) => {
                store.commit('setGithubRepos', d)
            })
    }
}

export default new UserService()
