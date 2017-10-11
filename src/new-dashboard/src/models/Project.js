import APIService from '../services/APIService'
import store from '../store'

export default class Project {
    constructor (name, id, type) {
        this.name = name
        this.id = id
        this.builds = []
        this.commits = []
        this.state = 'finished'
        this.type = type
    }

    isGit () {
        return this.type === 'github' || this.type === 'gerrit'
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

    getBuild (number, restartCounter) {
        const b = this._getBuild(number, restartCounter)

        if (b) {
            return new Promise((resolve) => { resolve(b) })
        }

        return APIService.get('/api/dashboard/build')
        .then((build) => {
            this._addBuild(build)
            return build
        })
    }

    _getBuild (number, restartCounter) {
        for (let b of this.builds) {
            if (b.number === number && b.restartCounter === restartCounter) {
                return b
            }
        }
    }

    _addBuild (build) {
        if (!build) {
            return
        }

        store.commit('addBuild', this, build)
    }
}
