import Notification from '../models/Notification'
import NotificationService from '../services/NotificationService'
import APIService from '../services/APIService'

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
    }

    loadHistory () {
        const url = 'project/' +
                    this.job.project.id +
                    '/job/' +
                    this.job.id +
                    '/test/history?suite=' +
                    encodeURIComponent(this.suite) +
                    '&test=' +
                    encodeURIComponent(this.name)

        return APIService.get(url)
            .then((history) => {
                this.history = history
            })
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
    }
}
