import NewAPIService from '../services/NewAPIService'
import NotificationService from '../services/NotificationService'
import Notification from '../models/Notification'
import store from '../store'
import router from '../router'
import events from '../events'

export default class Project {
    constructor (name, id, type, userrole) {
        this.name = name
        this.id = id
        this.builds = []
        this.commits = []
        this.state = 'finished'
        this.type = type
        this.secrets = null
        this.collaborators = null
        this.roles = null
        this.userrole = userrole
        this.tokens = null
        this.numQueuedJobs = 0
        this.numScheduledJobs = 0
        this.numRunningJobs = 0
    }

    isGit () {
        return this.type === 'github' || this.type === 'gerrit'
    }

    userHasOwnerRights () {
        return this.userrole === 'Owner'
    }

    userHasAdminRights () {
        return this.userHasOwnerRights() || this.userrole === 'Administrator'
    }

    userHasDevRights () {
        console.log(this.userHasAdminRights() || this.userrole === 'Developer')
        return this.userHasAdminRights() || this.userrole === 'Developer'
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

        return NewAPIService.get(`projects/${this.id}/builds/${number}/${restartCounter}`)
            .then((jobs) => {
                this._addJobs(jobs)
                return this._getBuild(number, restartCounter)
            })
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
    }

    removeCollaborator (co) {
        return NewAPIService.delete(`projects/${this.id}/collaborators/${co.id}`)
            .then((response) => {
                NotificationService.$emit('NOTIFICATION', new Notification(response, 'done'))
                this._reloadCollaborators()
            })
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
    }

    deleteToken (id) {
        return NewAPIService.delete(`projects/${this.id}/tokens/${id}`)
        .then((response) => {
            NotificationService.$emit('NOTIFICATION', new Notification(response, 'done'))
            this._reloadTokens()
        })
        .catch((err) => {
            NotificationService.$emit('NOTIFICATION', new Notification(err))
        })
    }

    addToken (description) {
        const d = { description: description, scope_pull: true, scope_push: true }
        return NewAPIService.post(`projects/${this.id}/tokens`, d)
        .then((response) => {
            const token = response.data.token
            this._reloadTokens()
            return token
        })
        .catch((err) => {
            NotificationService.$emit('NOTIFICATION', new Notification(err))
        })
    }

    triggerBuild (branchOrSha, env) {
        const d = { branch_or_sha: branchOrSha, env: env }
        return NewAPIService.post(`projects/${this.id}/trigger`, d)
        .then((r) => {
            NotificationService.$emit('NOTIFICATION', new Notification(r))
            const d = r.data
            router.push(`/project/${this.name}/build/${d.build.build_number}/${d.build.restartCounter}/`)
        })
        .catch((err) => {
            NotificationService.$emit('NOTIFICATION', new Notification(err))
        })
    }

    addCollaborator (username, role) {
        const d = { username: username, role: role }
        return NewAPIService.post(`projects/${this.id}/collaborators`, d)
        .then((response) => {
            NotificationService.$emit('NOTIFICATION', new Notification(response))
            this._reloadCollaborators()
        })
        .catch((err) => {
            NotificationService.$emit('NOTIFICATION', new Notification(err))
        })
    }

    updateCollaborator (co) {
        const d = { role: co.role }
        return NewAPIService.put(`projects/${this.id}/collaborators/${co.id}`, d)
        .then((response) => {
            NotificationService.$emit('NOTIFICATION', new Notification(response))
            this._reloadCollaborators()
        })
        .catch((err) => {
            NotificationService.$emit('NOTIFICATION', new Notification(err))
            this._reloadCollaborators()
        })
    }

    _loadJobs () {
        return NewAPIService.get(`projects/${this.id}/jobs/`)
        .then((response) => {
            store.commit('addJobs', response)
            events.listenJobs(this)
        })
    }

    _loadCollaborators () {
        if (this.collaborators) {
            return
        }

        this._reloadCollaborators()
    }

    _reloadCollaborators () {
        return NewAPIService.get(`projects/${this.id}/collaborators`)
            .then((collaborators) => {
                store.commit('setCollaborators', { project: this, collaborators: collaborators })
            })
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
    }

    _loadSecrets () {
        if (this.secrets) {
            return
        }

        this._reloadSecrets()
    }

    _reloadSecrets () {
        return NewAPIService.get(`projects/${this.id}/secrets`)
            .then((secrets) => {
                store.commit('setSecrets', { project: this, secrets: secrets })
            })
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
    }

    _loadRoles () {
        if (this.roles) {
            return
        }

        this._reloadRoles()
    }

    _reloadRoles () {
        return NewAPIService.get(`projects/${this.id}/collaborators/roles`)
            .then((roles) => {
                store.commit('setRoles', { project: this, roles: roles })
            })
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
    }

    _loadTokens () {
        if (this.tokens) {
            return
        }

        this._reloadTokens()
    }

    _reloadTokens () {
        return NewAPIService.get(`projects/${this.id}/tokens`)
            .then((tokens) => {
                store.commit('setTokens', { project: this, tokens: tokens })
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
