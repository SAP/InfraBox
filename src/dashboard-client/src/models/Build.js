import APIService from '../services/APIService'
import NotificationService from '../services/NotificationService'
import Notification from '../models/Notification'
import router from '../router'

export default class Build {
    constructor (id, number, restartCounter, commit, pr, project) {
        this.id = id
        this.number = number
        this.restartCounter = restartCounter
        this.state = null
        this.jobs = []
        this.commit = commit
        this.startDate = null
        this.endDate = null
        this.pull_request = pr
        this.project = project
        this.numQueuedJobs = 0
        this.numScheduledJobs = 0
        this.numRunningJobs = 0
    }

    getJob (jobId) {
        const j = this._getJob(jobId)

        if (j) {
            return new Promise((resolve) => { resolve(j) })
        }

        return null
    }

    _getJob (jobName) {
        for (let j of this.jobs) {
            if (j.name === jobName) {
                return j
            }
        }

        return null
    }

    abort () {
        return APIService.get(`project/${this.project.id}/build/${this.id}/kill`)
            .then((message) => {
                NotificationService.$emit('NOTIFICATION', new Notification(message, 'done'))
            })
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
    }

    restart () {
        return APIService.get(`project/${this.project.id}/build/${this.id}/restart`)
            .then((message) => {
                NotificationService.$emit('NOTIFICATION', new Notification(message, 'done'))
                router.push(`/project/${this.project.name}/build/${this.number}/${message.data.build.restartCounter}/`)
            })
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
    }

    clearCache () {
        return APIService.get(`project/${this.project.id}/build/${this.id}/cache/clear`)
            .then((message) => {
                NotificationService.$emit('NOTIFICATION', new Notification(message, 'done'))
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
                break
            }

            if (j.state === 'error' || j.state === 'failure' || j.state === 'killed') {
                this.state = j.state
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
            this.endDate = null
            return
        }

        for (let j of this.jobs) {
            if (!this.endDate) {
                this.endDate = j.endDate
            }

            if (j.endDate > this.endDate) {
                this.endDate = j.endDate
            }
        }
    }

    _updateStats () {
        let numQueuedJobs = 0
        let numScheduledJobs = 0
        let numRunningJobs = 0

        if (this.state === 'running') {
            for (let j of this.jobs) {
                if (j.state === 'queued') {
                    numQueuedJobs += 1
                } else if (j.state === 'scheduled') {
                    numScheduledJobs += 1
                } else if (j.state === 'running') {
                    numRunningJobs += 1
                }
            }
        }

        this.numQueuedJobs = numQueuedJobs
        this.numScheduledJobs = numScheduledJobs
        this.numRunningJobs = numRunningJobs
    }

    _updateState () {
        this._updateBuildState()
        this._updateStartDate()
        this._updateEndDate()
        this._updateStats()
    }
}
