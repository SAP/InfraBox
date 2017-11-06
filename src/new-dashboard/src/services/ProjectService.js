import store from '../store'

import APIService from '../services/APIService'
import NotificationService from './NotificationService'
import Notification from '../models/Notification'
import router from '../router'

class ProjectService {
    constructor () {
        this.resolve = null
        this.reject = null
        this.promise = new Promise((resolve, reject) => {
            this.resolve = resolve
            this.reject = reject
        })
    }

    findProjectByName (name) {
        return this.promise.then(() => {
            return this._findProjectByName(name)
        })
    }

    init () {
        this._loadProjects()
    }

    deleteProject (id) {
        APIService.delete(`project/${id}`)
        .then((response) => {
            NotificationService.$emit('NOTIFICATION', new Notification(response))
            store.commit('deleteProject', id)
        })
    }

    addProject (name, priv, type, githubRepoName) {
        const d = { name: name, type: type, private: priv, github_repo_name: githubRepoName }
        return APIService.post('project', d)
        .then((response) => {
            NotificationService.$emit('NOTIFICATION', new Notification(response))
            this._loadProjects()
            router.push('/')
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
        return APIService.get('project')
        .then((response) => {
            store.commit('setProjects', response)
            this.resolve()
        }).catch((err) => {
            this.reject(err)
        })
    }
}

export default new ProjectService()
