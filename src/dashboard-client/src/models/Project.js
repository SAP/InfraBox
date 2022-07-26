import NewAPIService from '../services/NewAPIService'
import NotificationService from '../services/NotificationService'
import Notification from '../models/Notification'
import store from '../store'
import router from '../router'
import events from '../events'

export default class Project {
    constructor (name, id, type, userrole, pub) {
        this.name = name
        this.id = id
        this.builds = []
        this.commits = []
        this.state = 'finished'
        this.type = type
        this.secrets = null
        this.vault = null
        this.pattern = null
        this.cronjobs = null
        this.collaborators = null
        this.roles = null
        this.userrole = userrole
        this.tokens = null
        this.numQueuedJobs = 0
        this.numScheduledJobs = 0
        this.numRunningJobs = 0
        this.sshkeys = null
        this.public = pub
    }

    isGit () {
        return this.type === 'github' || this.type === 'gerrit'
    }

    userHasOwnerRights () {
        return this.userrole === 'Owner'
    }

    userHasAdminRights () {
        return this.userHasOwnerRights() || this.userrole === 'Administrator' || store.state.user.hasWriteAccess()
    }

    userHasDevRights () {
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

    loadBuilds (from, to, sha, branch, cronjob, buildLimit) {
        let url = `projects/${this.id}/jobs/?from=${from}&to=${to}`

        if (sha) {
            url += `&sha=${sha}`
        }

        if (branch) {
            url += `&branch=${branch}`
        }

        if (cronjob) {
            url += `&cronjob=${cronjob}`
        }

        if (buildLimit) {
            url += `&build_limit=${buildLimit}`
        }

        return NewAPIService.get(url)
            .then((jobs) => {
                this._addJobs(jobs)
            })
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
    }

    getBuild (number, restartCounter) {
        const b = this._getBuild(number, restartCounter)

        if (b) {
            return new Promise((resolve) => { resolve(b) })
        }

        return this._loadBuild(number, restartCounter)
    }

    _loadBuild (number, restartCounter) {
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

    triggerBuild (branchOrSha, env, branch) {
        const d = { branch_or_sha: branchOrSha, env: env, branch: branch }
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

    _loadCronJobs () {
        if (this.cronjobs) {
            return
        }

        this._reloadCronJobs()
    }

    _reloadCronJobs () {
        return NewAPIService.get(`projects/${this.id}/cronjobs`)
            .then((cronjobs) => {
                store.commit('setCronJobs', { project: this, cronjobs: cronjobs })
            })
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
    }

    _loadSSHKeys () {
        if (this.sshkeys) {
            return
        }

        this._reloadSSHKeys()
    }

    _reloadSSHKeys () {
        return NewAPIService.get(`projects/${this.id}/sshkeys`)
            .then((sshkeys) => {
                store.commit('setSSHKeys', { project: this, sshkeys: sshkeys })
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

    _loadVault () {
        if (this.vault) {
            return
        }
        this._reloadVault()
    }
    _reloadVault () {
        return NewAPIService.get(`projects/${this.id}/vault`)
            .then((vault) => {
                store.commit('setVault', {project: this, vault: vault})
            })
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
    }

    _loadPattern () {
        if (this.pattern) {
            return
        }
        this._reloadPattern()
    }
    _reloadPattern () {
        return NewAPIService.get(`projects/${this.id}/pattern`)
            .then((pattern) => {
                store.commit('setPattern', {project: this, pattern: pattern})
            })
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
    }
}
