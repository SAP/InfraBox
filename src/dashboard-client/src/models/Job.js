import events from '../events'
import Notification from '../models/Notification'
import NotificationService from '../services/NotificationService'
import NewAPIService from '../services/NewAPIService'
import store from '../store'
import router from '../router'
import moment from 'moment'

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
        this.labels = {}
    }

    setEndTime (end) {
        if (!this.startTime) {
            this.startTime = end
        }

        const dur = (end.getTime() - this.startTime.getTime()) / 1000
        this.duration = Math.max(Math.round(dur), 0)
    }

    addLabel (level) {
        if (!this.labels[level]) {
            this.labels[level] = 0
        }

        this.labels[level] += 1
    }

    addLine (line) {
        line += '\n'
        this.lines_raw.push(line)

        if (this.lines_raw.length > 200) {
            this.lines_raw.splice(0, 1)
        }

        this.linesInSection += 1
    }

    generateHtml (job) {
        const url = `${NewAPIService.api}projects/${job.project.id}/jobs/${job.id}/console`
        let t = ''

        if (this.lines_raw.length >= 200) {
            t += `Output too large, only showing last 200 lines (Full console output):\n`
        }

        for (let l of this.lines_raw) {
            t += l
        }

        t = this.escapeHtml(t)

        this.lines_html = t
        const convert = new Convert()
        this.lines_html = convert.toHtml(t)
        this.lines_html = this.lines_html.replace('Full console output', `<a href="${url}" target="_blank">Full console output</a>`)
    }

    escapeHtml (text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        }

        return text.replace(/[&<>'']/g, (m) => map[m])
    }
}

export default class Job {
    constructor (
        id, name, state,
        startDate, endDate, build, project,
        dependencies, message, definition, nodeName, avgCpu, restarted) {
        this.id = id
        this.name = name
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
        this.archive = []
        this.currentSection = null
        this.linesProcessed = 0
        this.hasLogsAvailable = false
        this.message = message
        this.definition = definition
        this.nodeName = nodeName
        this.avgCpu = avgCpu
        this.restarted = restarted
    }

    _getTime (d) {
        // This date is only used to calculate duration and show local time in console log.
        // We only care about time, so it's ok to ignore date.
        const t = new Date('1970-01-01T' + d + 'Z')

        return t
    }

    _addSection (line, date) {
        let idx = line.indexOf('|##')
        const header = line.substr(idx + 3)

        this.currentSection.setEndTime(date)
        this.currentSection.generateHtml(this)

        this.currentSection = new Section(this.linesProcessed, header, date, this.sections.length)
        this.linesProcessed++
        this.sections.push(this.currentSection)
    }

    _addStepSection (line, date) {
        let idx = line.indexOf('|Step')
        const header = line.substr(idx + 5)

        this.currentSection.setEndTime(date)
        this.currentSection.generateHtml(this)

        this.currentSection = new Section(this.linesProcessed, header, date, this.sections.length)
        this.linesProcessed++
        this.sections.push(this.currentSection)
    }

    _addLabeledLine (line, date) {
        let idx = line.indexOf('[level=')
        if (idx >= 0) {
            let end = line.indexOf(']')
            idx += 7
            const level = line.substr(idx, end - idx)
            this.currentSection.addLabel(level)
            // line = header.substr(end + 2, header.length - end)
        }

        this.currentSection.addLine(line)
        this.linesProcessed++
    }

    _addLine (line) {
        let idx = line.indexOf('|')

        let date = null
        if (idx > 0) {
            const d = line.substr(0, idx)
            date = this._getTime(d)
        }

        if (!this.currentSection) {
            this.currentSection = new Section(this.linesProcessed, 'Prepare Job', date, 0)
            this.sections.push(this.currentSection)
        }

        // Check for labled lines
        idx = line.indexOf('|###')
        if (idx >= 0 && idx < 10) {
            return this._addLabeledLine(line, date)
        }

        idx = line.indexOf('|##')
        if (idx >= 0 && idx < 10) {
            return this._addSection(line, date)
        }

        idx = line.indexOf('|Step')
        if (idx >= 0 && idx < 10) {
            return this._addStepSection(line, date)
        }

        // Replace UTC time with local time
        idx = line.indexOf('|')
        if (idx > 0) {
            let localTime = moment(date).format('HH:mm:ss')
            line = localTime + line.substr(idx)
        }

        this.currentSection.addLine(line)
        this.linesProcessed++

        if (!this.hasLogsAvailable) {
            this.hasLogsAvailable = true
        }
    }

    _addLines (lines) {
        for (let line of lines) {
            if (line === '') {
                continue
            }

            this._addLine(line)
        }

        if (this.currentSection) {
            this.currentSection.generateHtml(this)
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

    loadArchive () {
        return NewAPIService.get(`projects/${this.project.id}/jobs/${this.id}/archive`)
            .then((archive) => {
                store.commit('setArchive', { job: this, archive: archive })
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
                        stat.values.push({ cpu: Math.round(o.cpu), date: i, mem: Math.round(o.mem) })
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

    downloadAllArchive () {
        const url = `projects/${this.project.id}/jobs/${this.id}/archive/download/all`
        NewAPIService.openAPIUrl(url)
    }

    downloadArchive (filename, view = false) {
        const url = `projects/${this.project.id}/jobs/${this.id}/archive/download?filename=${filename}&view=${view}`
        NewAPIService.openAPIUrl(url)
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification('It seems the archived file was deleted from the server'))
                console.log(err)
            })
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
                NotificationService.$emit('NOTIFICATION', new Notification(message, 'done'))
                return this.project._loadBuild(this.build.number, this.build.restartCounter)
            }).then((build) => {
                let arr = this.name.split('/')
                let frontName = arr.slice(0, arr.length - 1)
                let lastName = arr[arr.length - 1]
                let a = lastName.split('.')
                let name = a[0] + '.'

                if (a.length > 1) {
                    name += (parseInt(a[1]) + 1).toString()
                } else {
                    name += '1'
                }

                if (frontName.length > 0) {
                    name = '/' + name
                    name = frontName.join('/') + name
                }

                router.push({
                    name: 'JobDetail',
                    params: {
                        projectName: encodeURIComponent(this.project.name),
                        buildNumber: this.build.number,
                        buildRestartCounter: this.build.restartCounter,
                        jobName: name
                    }
                })
            })
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
    }

    rerun () {
        return NewAPIService.get(`projects/${this.project.id}/jobs/${this.id}/rerun`)
            .then((message) => {
                NotificationService.$emit('NOTIFICATION', new Notification(message, 'done'))
                return this.project._loadBuild(this.build.number, this.build.restartCounter)
            }).then((build) => {
                let a = this.name.split('.')
                let name = a[0] + '.'

                if (a.length > 1) {
                    name += (parseInt(a[1]) + 1).toString()
                } else {
                    name += '1'
                }
                router.push({
                    name: 'JobDetail',
                    params: {
                        projectName: encodeURIComponent(this.project.name),
                        buildNumber: this.build.number,
                        buildRestartCounter: this.build.restartCounter,
                        jobName: name
                    }
                })
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
