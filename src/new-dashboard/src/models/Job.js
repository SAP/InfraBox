import events from '../events'
const Convert = require('ansi-to-html')

class Section {
    linesInSection = 0
    duration = 0

    constructor (line, text, startTime) {
        this.line = line
        this.text = text
        this.startTime = startTime
        this.lines_raw = []
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

        if (this.lines_raw.length > 500) {
            this.lines_raw.splice(0, 1)
        }

        this.linesInSection += 1
    }

    generateHtml () {
        let t = ''

        if (this.lines_raw.length >= 500) {
            t += 'Output too large, only showing last 500 lines:\n'
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
            dependencies) {
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

            if (idx >= 0) {
                header = line.substr(idx + 3)
                const d = line.substr(0, idx)
                date = this._getTime(d)
                isSection = true
            }

            idx = line.indexOf('|Step')
            if (idx >= 0) {
                header = line.substr(idx + 5)
                const d = line.substr(0, idx)
                date = this._getTime(d)
                isSection = true
            }

            if (isSection) {
                if (this.currentSection) {
                    this.currentSection.setEndTime(date)
                }
                this.currentSection = new Section(this.linesProcessed, header, date)
                this.linesProcessed++
                this.sections.push(this.currentSection)
            } else {
                if (!this.currentSection) {
                    this.currentSection = new Section(this.linesProcessed, 'Console Output', date)
                    this.sections.push(this.currentSection)
                }

                this.currentSection.addLine(line)
                this.linesProcessed++
            }

            this.currentSection.generateHtml()
        }
    }

    listenConsole () {
        events.listenConsole(this.id)
    }
}
