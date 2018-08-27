import Notification from '../models/Notification'
import NotificationService from '../services/NotificationService'
import NewAPIService from '../services/NewAPIService'

export default class Test {
    constructor (opts, job) {
        this.name = opts.name
        this.suite = opts.suite
        this.message = opts.message
        this.stack = opts.stack
        this.state = opts.state
        this.history = null
        this.duration = opts.duration
        this.job = job
        this.timestamp = opts.timestamp
    }

    loadHistory () {
        const url = 'projects/' +
                    this.job.project.id +
                    '/jobs/' +
                    this.job.id +
                    '/tests/history?suite=' +
                    encodeURIComponent(this.suite) +
                    '&test=' +
                    encodeURIComponent(this.name)

        return NewAPIService.get(url)
            .then((history) => {
                this.history = history
            })
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
    }
}
