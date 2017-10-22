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
    }
}
