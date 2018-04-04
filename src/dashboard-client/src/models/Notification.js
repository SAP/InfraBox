class Notification {
    constructor (n, icon) {
        if (!n) {
            console.log(new Error().stack)
        }

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
