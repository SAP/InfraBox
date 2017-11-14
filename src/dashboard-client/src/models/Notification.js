class Notification {
    constructor (n, icon) {
        this.icon = icon || n.icon || 'error'

        let message = 'Internal Error occured'
        if (n.body && n.body.message) {
            message = n.body.message
        }

        if (n.message) {
            message = n.message
        }

        this.message = message
    }
}

export default Notification
