import store from '../store'

import NewAPIService from '../services/NewAPIService'
import NotificationService from './NotificationService'
import Notification from '../models/Notification'
import router from '../router'

class ProjectService {
    init () {
        this._loadProjects()
    }

    deleteProject (id) {
        NewAPIService.delete(`projects/${id}`)
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
        return NewAPIService.post('projects', d)
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
        const encodedName = encodeURIComponent(name)
        const decodedName = decodeURIComponent(name)

        for (let p of store.state.projects) {
            if (p.name === decodedName) {
                return new Promise((resolve) => { resolve(p) })
            }
        }

        return NewAPIService.get(`projects/name/${encodedName}`)
            .then((project) => {
                store.commit('addProjects', [project])

                for (let p of store.state.projects) {
                    if (p.name === decodedName) {
                        return p
                    }
                }
            })
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
    }

    _loadProjects () {
        return NewAPIService.get('projects/')
            .then((response) => {
                store.commit('addProjects', response)
            })
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
    }
}

export default new ProjectService()
