export default class Build {
    constructor (id, number, restartCounter, commit, pr) {
        this.id = id
        this.number = number
        this.restartCounter = restartCounter
        this.state = 'running'
        this.jobs = []
        this.commit = commit
        this.start_date = null
        this.end_date = null
        this.pull_request = pr
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
        if (!this.start_date) {
            this.start_date = this.jobs[0].start_date
        }

        for (let j of this.jobs) {
            if (j.start_date < this.start_date) {
                this.start_date = j.start_date
            }
        }
    }

    _updateEndDate () {
        if (this._isActive()) {
            return
        }

        for (let j of this.jobs) {
            if (j.end_date > this.end_date) {
                this.end_date = j.end_date
            }
        }
    }

    _updateState () {
        this._updateBuildState()
        this._updateStartDate()
        this._updateEndDate()
    }
}
