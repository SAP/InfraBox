import store from '../store'
import events from '../events'

import APIService from '../services/APIService'

class ProjectService {
    init () {
        this.loaded = this._loadProjects()
    }

    findProjectByName (name) {
        return this.loaded.then(() => {
            return this._findProjectByName(name)
        })
    }

    _findProjectByName (name) {
        for (let p of store.state.projects) {
            if (p.name === name) {
                return new Promise((resolve) => { resolve(p) })
            }
        }

        return new Promise((resolve, reject) => { reject(new Error('Project not found')) })
    }

    _loadProjects () {
        return APIService.get('/api/dashboard/project')
        .then((response) => {
            for (let p of response) {
                store.commit('addProject', p)
                events.listenJobs(p)
            }
        })
    }
}

export default new ProjectService()
