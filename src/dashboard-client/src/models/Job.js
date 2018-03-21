import events from '../events'
import Notification from '../models/Notification'
import NotificationService from '../services/NotificationService'
import NewAPIService from '../services/NewAPIService'
import store from '../store'
const Convert = require('ansi-to-html')

class Section {
    linesInSection = 0
    duration = 0
    id = 0

    constructor (line, text, startTime, id) {
        this.line = line
        this.text = text
        this.startTime = startTime
        this.lines_raw = []
        this.id = id
    }

    setEndTime (end) {
        if (!this.startTime) {
            this.startTime = end
        }

        const dur = (end.getTime() - this.startTime.getTime()) / 1000
        this.duration = Math.max(Math.round(dur), 0)
    }

    addLine (line) {
        line += '\n'
        this.lines_raw.push(line)

        if (this.lines_raw.length > 200) {
            this.lines_raw.splice(0, 1)
        }

        this.linesInSection += 1
    }

    generateHtml () {
        let t = ''

        if (this.lines_raw.length >= 200) {
            t += 'Output too large, only showing last 200 lines:\n'
        }

        for (let l of this.lines_raw) {
            t += l
        }

        t = this.escapeHtml(t)

        this.lines_html = t
        const convert = new Convert()
        this.lines_html = convert.toHtml(t)
    }

    escapeHtml (text) {
        const map = {
            '&': '&amp',
            '<': '&lt',
            '>': '&gt',
            '"': '&quot',
            "'": '&#039'
        }

        return text.replace(/[&<>'']/g, (m) => map[m])
    }
}

export default class Job {
    constructor (id, name, cpu, memory, state,
            startDate, endDate, build, project,
            dependencies, message) {
        this.id = id
        this.name = name
        this.cpu = cpu
        this.memory = memory
        this.state = state
        this.startDate = startDate
        this.endDate = endDate
        this.build = build
        this.project = project
        this.dependencies = dependencies || []
        this.sections = []
        this.badges = []
        this.tests = []
        this.stats = []
        this.tabs = []
        this.currentSection = null
        this.linesProcessed = 0
        this.message = message
    }

    _getTime (d) {
        const parts = d.split(':')
        const t = new Date()

        t.setHours(parseInt(parts[0], 10))
        t.setMinutes(parseInt(parts[1], 10))
        t.setSeconds(parseInt(parts[2], 10))

        return t
    }

    _addLines (lines) {
        for (let line of lines) {
            if (line === '') {
                continue
            }

            let header = ''
            let isSection = false

            let idx = line.indexOf('|##')
            let date = null

            if (idx >= 0 && idx < 10) {
                header = line.substr(idx + 3)
                const d = line.substr(0, idx)
                date = this._getTime(d)
                isSection = true
            }

            idx = line.indexOf('|Step')
            if (idx >= 0 && idx < 10) {
                header = line.substr(idx + 5)
                const d = line.substr(0, idx)
                date = this._getTime(d)
                isSection = true
            }

            if (isSection) {
                if (this.currentSection) {
                    this.currentSection.setEndTime(date)
                    this.currentSection.generateHtml()
                }
                this.currentSection = new Section(this.linesProcessed, header, date, this.sections.length)
                this.linesProcessed++
                this.sections.push(this.currentSection)
            } else {
                if (!this.currentSection) {
                    this.currentSection = new Section(this.linesProcessed, 'Prepare Job', date, 0)
                    this.sections.push(this.currentSection)
                }

                this.currentSection.addLine(line)
                this.linesProcessed++
            }
        }

        if (this.currentSection) {
            this.currentSection.generateHtml()
        }
    }

    getTest (name, suite) {
        this.loadTests()
        for (const t of this.tests) {
            if (t.name === name && t.suite === suite) {
                return t
            }
        }

        return null
    }

    loadBadges () {
        return NewAPIService.get(`projects/${this.project.id}/jobs/${this.id}/badges`)
            .then((badges) => {
                store.commit('setBadges', { job: this, badges: badges })
            })
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
    }

    loadConsole () {
        if (this.sections.length) {
            return
        }

        return NewAPIService.get(`projects/${this.project.id}/jobs/${this.id}/console`)
            .then((console) => {
                store.commit('setConsole', { job: this, console: console })
                events.listenConsole(this.id)
            })
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
    }

    loadTabs () {
        return NewAPIService.get(`projects/${this.project.id}/jobs/${this.id}/tabs`)
            .then((tabs) => {
                store.commit('setTabs', { job: this, tabs: tabs })
            })
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
    }

    loadTests () {
        return NewAPIService.get(`projects/${this.project.id}/jobs/${this.id}/testruns`)
            .then((tests) => {
                store.commit('setTests', { job: this, tests: tests })
            })
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
    }

    loadStats () {
        return NewAPIService.get(`projects/${this.project.id}/jobs/${this.id}/stats`)
            .then((values) => {
                const stats = []
                for (const n of Object.keys(values)) {
                    const stat = {
                        name: n,
                        values: []
                    }

                    let i = 0
                    for (const o of values[n]) {
                        stat.values.push({ cpu: o.cpu, date: i, mem: o.mem })
                        ++i
                    }

                    stats.push(stat)
                }

                store.commit('setStats', { job: this, stats: stats })
            })
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
    }

    downloadDataOutput () {
        const url = `projects/${this.project.id}/jobs/${this.id}/output`
        NewAPIService.openAPIUrl(url)
    }

    listenConsole () {
        events.listenConsole(this.id)
    }

    downloadOutput () {
        const url = `projects/${this.project.id}/jobs/${this.id}/console`
        NewAPIService.openAPIUrl(url)
    }

    abort () {
        return NewAPIService.get(`projects/${this.project.id}/jobs/${this.id}/abort`)
            .then((message) => {
                NotificationService.$emit('NOTIFICATION', new Notification(message, 'done'))
            })
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
    }

    restart () {
        return NewAPIService.get(`projects/${this.project.id}/jobs/${this.id}/restart`)
            .then((message) => {
                console.log(message)
                NotificationService.$emit('NOTIFICATION', new Notification(message, 'done'))

                this.sections = []
                this.currentSection = null
                this.linesProcessed = 0
                this.endDate = null
                this.startDate = null
                this.message = null
                this.listenConsole()
            })
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
    }

    clearCache () {
        return NewAPIService.get(`projects/${this.project.id}/jobs/${this.id}/cache/clear`)
            .then((message) => {
                NotificationService.$emit('NOTIFICATION', new Notification(message, 'done'))
            })
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
    }
}
