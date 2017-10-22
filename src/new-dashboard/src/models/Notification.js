class Notification {
    constructor (n) {
        console.log(n)
        let message = 'Internal Error occured'
        let type = 'error'
        if (n.body && n.body.message) {
            message = n.body.message
        }

        if (n.message) {
            message = n.message
        }

        if (n.type) {
            type = n.type
        }

        this.message = message
        this.type = type
    }
}

export default Notification
