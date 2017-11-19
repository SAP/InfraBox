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

    findProjectByName (name) {
        for (let p of store.state.projects) {
            if (p.name === name) {
                return new Promise((resolve) => { resolve(p) })
            }
        }

        return APIService.get(`project/name/${name}`)
            .then((project) => {
                store.commit('addProjects', [project])
                return project
            })
    }

    _loadProjects () {
        return APIService.get('project')
        .then((response) => {
            console.log(response)
            store.commit('addProjects', response)
        })
    }
}

export default new ProjectService()
