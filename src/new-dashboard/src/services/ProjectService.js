import store from '../store'

import APIService from '../services/APIService'
import NotificationService from './NotificationService'
import Notification from '../models/Notification'
import router from '../router'

class ProjectService {
    init () {
        this.loaded = this._loadProjects()
    }

    findProjectByName (name) {
        return this.loaded.then(() => {
            return this._findProjectByName(name)
        })
    }

    loadProjects () {
        return this.loaded
    }

    deleteProject (id) {
        APIService.delete(`project/${id}`)
        .then((response) => {
            NotificationService.$emit('NOTIFICATION', new Notification(response))
            store.commit('deleteProject', id)
        })
    }

    addProject (name, priv, type) {
        const d = { name: name, type: type, private: priv }
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
        })
    }
}

export default new ProjectService()
