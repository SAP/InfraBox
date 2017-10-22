import APIService from '../services/APIService'
import store from '../store'
import NotificationService from '../services/NotificationService'
import Notification from '../models/Notification'

export default class Project {
    constructor (name, id, type) {
        this.name = name
        this.id = id
        this.builds = []
        this.commits = []
        this.state = 'finished'
        this.type = type
        this.secrets = null
        this.collaborators = null
        this.tokens = null
    }

    isGit () {
        return this.type === 'github' || this.type === 'gerrit'
    }

    getActiveBuilds () {
        const builds = []
        for (let b of this.builds) {
            if (b.state === 'running') {
                builds.push(b)
            }
        }

        return builds
    }

    getBuild (number, restartCounter) {
        const b = this._getBuild(number, restartCounter)

        if (b) {
            return new Promise((resolve) => { resolve(b) })
        }

        return APIService.get(`/api/dashboard/project/${this.id}/build/${number}/${restartCounter}`)
            .then((jobs) => {
                this._addJobs(jobs)
                return this._getBuild(number, restartCounter)
            })
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
    }

    _loadCollaborators () {
        if (this.collaborators) {
            return
        }

        return APIService.get(`/api/dashboard/project/${this.id}/collaborators`)
            .then((collaborators) => {
                store.commit('addCollaborators', { project: this, collaborators: collaborators })
            })
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
    }

    _loadSecrets () {
        if (this.secrets) {
            return
        }

        return APIService.get(`/api/dashboard/project/${this.id}/secrets`)
            .then((secrets) => {
                store.commit('addSecrets', { project: this, secrets: secrets })
            })
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
    }

    _loadTokens () {
        if (this.secrets) {
            return
        }

        return APIService.get(`/api/dashboard/project/${this.id}/tokens`)
            .then((tokens) => {
                store.commit('addTokens', { project: this, tokens: tokens })
            })
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
    }

    _getBuild (number, restartCounter) {
        for (let b of this.builds) {
            if (b.number === number && b.restartCounter === restartCounter) {
                return b
            }
        }
    }

    _addJobs (jobs) {
        if (!jobs) {
            return
        }

        store.commit('addJobs', jobs)
    }
}
