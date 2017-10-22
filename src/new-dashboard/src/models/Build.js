import APIService from '../services/APIService'
import NotificationService from '../services/NotificationService'
import Notification from '../models/Notification'

export default class Build {
    constructor (id, number, restartCounter, commit, pr, project) {
        this.id = id
        this.number = number
        this.restartCounter = restartCounter
        this.state = 'running'
        this.jobs = []
        this.commit = commit
        this.startDate = null
        this.endDate = null
        this.pull_request = pr
        this.project = project
    }

    abort () {
        return APIService.get(`/api/dashboard/project/${this.project.id}/build/${this.id}/kill`)
            .then((message) => {
                NotificationService.$emit('NOTIFICATION', new Notification(message))
            })
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
    }

    restart () {
        return APIService.get(`/api/dashboard/project/${this.project.id}/build/${this.id}/restart`)
            .then((message) => {
                NotificationService.$emit('NOTIFICATION', new Notification(message))
            })
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
    }

    clearCache () {
        return APIService.get(`/api/dashboard/project/${this.project.id}/build/${this.id}/cache/clear`)
            .then((message) => {
                NotificationService.$emit('NOTIFICATION', new Notification(message))
            })
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
    }

    _updateBuildState () {
        this.state = 'finished'

        for (let j of this.jobs) {
            if (j.state === 'queued' || j.state === 'scheduled' || j.state === 'running') {
                this.state = 'running'
                return
            }

            if (j.state === 'error' || j.state === 'failure' || j.state === 'killed') {
                this.state = 'failure'
            }
        }
    }

    _isActive () {
        return this.state === 'queued' || this.state === 'scheduled' || this.state === 'running'
    }

    _updateStartDate () {
        if (!this.startDate) {
            this.startDate = this.jobs[0].startDate
        }

        for (let j of this.jobs) {
            if (!j.startDate) {
                continue
            }

            if (j.startDate < this.startDate) {
                this.startDate = j.startDate
            }
        }
    }

    _updateEndDate () {
        if (this._isActive()) {
            return
        }

        for (let j of this.jobs) {
            if (j.endDate > this.endDate) {
                this.endDate = j.endDate
            }
        }
    }

    _updateState () {
        this._updateBuildState()
        this._updateStartDate()
        this._updateEndDate()
    }
}
