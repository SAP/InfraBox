import store from '../store'

import APIService from '../services/APIService'
import NotificationService from './NotificationService'
import Notification from '../models/Notification'
import router from '../router'

class ProjectService {
    init () {
        this._loadProjects()
    }

    deleteProject (id) {
        APIService.delete(`projects/${id}`)
            .then((response) => {
                NotificationService.$emit('NOTIFICATION', new Notification(response))
                store.commit('deleteProject', id)
            })
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
    }

    addProject (name, priv, type, githubRepoName) {
        const d = { name: name, type: type, private: priv, github_repo_name: githubRepoName }
        return APIService.post('projects', d)
            .then((response) => {
                NotificationService.$emit('NOTIFICATION', new Notification(response))
                this._loadProjects()
                router.push('/')
            })
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
    }

    findProjectByName (name) {
        for (let p of store.state.projects) {
            if (p.name === name) {
                return new Promise((resolve) => { resolve(p) })
            }
        }

        return APIService.get(`projects/name/${name}`)
            .then((project) => {
                store.commit('addProjects', [project])
                return project
            })
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
    }

    _loadProjects () {
        return APIService.get('projects/')
            .then((response) => {
                store.commit('addProjects', response)
            })
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
    }
}

export default new ProjectService()
