import NewAPIService from '../services/NewAPIService'
import NotificationService from '../services/NotificationService'
import Notification from '../models/Notification'
import router from '../router'

export default class Build {
    constructor (id, number, restartCounter, isCronjob, commit, pr, project) {
        this.id = id
        this.number = number
        this.restartCounter = restartCounter
        this.state = 'finished'
        this.jobs = []
        this.commit = commit
        this.startDate = null
        this.endDate = null
        this.pull_request = pr
        this.project = project
        this.numQueuedJobs = 0
        this.numScheduledJobs = 0
        this.numRunningJobs = 0
        this.isCronjob = isCronjob
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
        return NewAPIService.get(`projects/${this.project.id}/builds/${this.id}/abort`)
            .then((message) => {
                NotificationService.$emit('NOTIFICATION', new Notification(message, 'done'))
            })
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
    }

    restart () {
        return NewAPIService.get(`projects/${this.project.id}/builds/${this.id}/restart`)
            .then((message) => {
                NotificationService.$emit('NOTIFICATION', new Notification(message, 'done'))
                router.push(`/project/${encodeURIComponent(this.project.name)}/build/${this.number}/${message.data.build.restartCounter}/`)
            })
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
    }

    clearCache () {
        return NewAPIService.get(`projects/${this.project.id}/builds/${this.id}/cache/clear`)
            .then((message) => {
                NotificationService.$emit('NOTIFICATION', new Notification(message, 'done'))
            })
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
    }

    _updateBuildState () {
        let states = {
            'error': false,
            'killed': false,
            'failure': false,
            'unstable': false
        }

        for (let j of this.jobs) {
            if (j.restarted) {
                continue
            }

            if (j.state === 'queued' || j.state === 'scheduled' || j.state === 'running') {
                this.state = 'running'
                return
            }

            states[j.state] = true
        }

        if (states.killed) {
            if (this.state !== 'killed') {
                this.state = 'killed'
            }
        } else if (states.error) {
            if (this.state !== 'error') {
                this.state = 'error'
            }
        } else if (states.failure) {
            if (this.state !== 'failure') {
                this.state = 'failure'
            }
        } else if (states.unstable) {
            if (this.state !== 'unstable') {
                this.state = 'unstable'
            }
        }
    }

    _isActive () {
        return this.state === 'queued' || this.state === 'scheduled' || this.state === 'running'
    }

    _updateStartDate () {
        for (let j of this.jobs) {
            if (!j.startDate) {
                continue
            }

            if (!this.startDate) {
                this.startDate = j.startDate
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
