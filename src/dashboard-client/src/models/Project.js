import APIService from '../services/APIService'
import NewAPIService from '../services/NewAPIService'
import NotificationService from '../services/NotificationService'
import Notification from '../models/Notification'
import store from '../store'
import router from '../router'

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
        this.numQueuedJobs = 0
        this.numScheduledJobs = 0
        this.numRunningJobs = 0
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

        return APIService.get(`project/${this.id}/build/${number}/${restartCounter}`)
            .then((jobs) => {
                this._addJobs(jobs)
                return this._getBuild(number, restartCounter)
            })
    }

    removeCollaborator (co) {
        return APIService.delete(`project/${this.id}/collaborators/${co.id}`)
            .then((response) => {
                NotificationService.$emit('NOTIFICATION', new Notification(response, 'done'))
                this._reloadCollaborators()
            })
    }

    deleteToken (id) {
        delete APIService.delete(`project/${this.id}/tokens/${id}`)
        .then((response) => {
            NotificationService.$emit('NOTIFICATION', new Notification(response, 'done'))
            this._reloadTokens()
        })
    }

    addToken (description) {
        const d = { description: description, scope_pull: true, scope_push: true }
        return APIService.post(`project/${this.id}/tokens`, d)
        .then((response) => {
            const token = response.data.token
            this._reloadTokens()
            return token
        })
    }

    triggerBuild (branchOrSha, env) {
        const d = { branch_or_sha: branchOrSha, env: env }
        return NewAPIService.post(`projects/${this.id}/trigger`, d)
        .then((r) => {
            console.log(r)
            NotificationService.$emit('NOTIFICATION', new Notification(r))
            const d = r.data
            router.push(`/project/${this.name}/build/${d.build.build_number}/${d.build.restartCounter}/`)
        })
    }

    addCollaborator (username) {
        const d = { username: username }
        return APIService.post(`project/${this.id}/collaborators`, d)
        .then((response) => {
            this._reloadCollaborators()
        })
    }

    _loadCollaborators () {
        if (this.collaborators) {
            return
        }

        this._reloadCollaborators()
    }

    _reloadCollaborators () {
        return APIService.get(`project/${this.id}/collaborators`)
            .then((collaborators) => {
                store.commit('setCollaborators', { project: this, collaborators: collaborators })
            })
    }

    _loadSecrets () {
        if (this.secrets) {
            return
        }

        this._reloadSecrets()
    }

    _reloadSecrets () {
        return APIService.get(`project/${this.id}/secrets`)
            .then((secrets) => {
                store.commit('setSecrets', { project: this, secrets: secrets })
            })
    }

    _loadTokens () {
        if (this.tokens) {
            return
        }

        this._reloadTokens()
    }

    _reloadTokens () {
        return APIService.get(`project/${this.id}/tokens`)
            .then((tokens) => {
                store.commit('setTokens', { project: this, tokens: tokens })
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

    _updateStats () {
        let numQueuedJobs = 0
        let numScheduledJobs = 0
        let numRunningJobs = 0

        for (let b of this.builds) {
            numQueuedJobs += b.numQueuedJobs
            numScheduledJobs += b.numScheduledJobs
            numRunningJobs += b.numRunningJobs
        }

        this.numQueuedJobs = numQueuedJobs
        this.numScheduledJobs = numScheduledJobs
        this.numRunningJobs = numRunningJobs
    }

    _updateState () {
        this._updateStats()

        if (this.builds) {
            this.state = this.builds[0].state
        } else {
            this.state = 'finished'
        }
    }
}
