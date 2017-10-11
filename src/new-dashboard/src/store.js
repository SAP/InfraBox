import Vue from 'vue'
import Vuex from 'vuex'
import events from './events'
import _ from 'underscore'

import Project from './models/Project'
import Build from './models/Build'

Vue.use(Vuex)

const state = {
    projects: []
}

function findProject (state, projectId) {
    for (let p of state.projects) {
        if (p.id === projectId) {
            return p
        }
    }

    return null
}

function findBuild (project, buildId) {
    for (let b of project.builds) {
        if (b.id === buildId) {
            return b
        }
    }

    return null
}

function findCommit (project, commitId) {
    for (let c of project.commits) {
        if (c.id === commitId) {
            return c
        }
    }

    return null
}

function findJob (build, jobId) {
    for (let j of build.jobs) {
        if (j.id === jobId) {
            return j
        }
    }

    return null
}

function updateProjectState (project) {
    if (project.builds) {
        project.state = project.builds[0].state
    } else {
        project.state = 'finished'
    }
}

function handleJobUpdate (state, event) {
    if (event.type === 'UPDATE') {
        const project = findProject(state, event.data.project.id)
        const build = findBuild(project, event.data.build.id)
        const job = findJob(build, event.data.job.id)

        const j = event.data.job
        job.state = j.state
        job.end_date = new Date(j.end_date)

        build._updateState()
        updateProjectState(project)
    } else if (event.type === 'INSERT') {
        const project = findProject(state, event.data.project.id)

        let commit = null

        if (project.isGit()) {
            // Update Commit
            findCommit(project, event.data.commit.id)
            if (event.data.commit) {
                if (!commit) {
                    commit = event.data.commit
                    project.commits.push(commit)
                }
            }
        }

        // Update Build
        let build = findBuild(project, event.data.build.id)
        if (!build) {
            build = new Build(event.data.build.id,
                              event.data.build.build_number,
                              event.data.build.restart_counter,
                              commit, event.data.pull_request)

            let builds = [build]

            for (let b of project.builds) {
                builds.push(b)
            }

            builds = _(builds)
                .chain()
                .sortBy((b) => { return b.restartCounter })
                .sortBy((b) => { return b.number })
                .value()
                .reverse()

            project.builds = builds
        }

        // Update Job
        const job = findJob(build, event.data.job.id)
        if (!job) {
            const d = event.data.job
            const job = {
                id: d.id,
                name: d.name,
                cpu: d.cpu,
                memory: d.memory,
                state: d.state,
                start_date: new Date(d.start_date),
                end_date: new Date(d.end_date)
            }
            build.jobs.push(job)
        }

        build._updateState(build)
        updateProjectState(project)
    }
}

function addProject (state, project) {
    state.projects.push(new Project(project.name, project.id, project.type))
}

function addBuild (state, project, build) {
    project.builds.push(build)
}

const mutations = {
    addProject,
    addBuild,
    handleJobUpdate
}

const getters = {}
const actions = {}

const store = new Vuex.Store({
    state,
    actions,
    mutations,
    getters
})

events.$on('NOTIFY_JOBS', (update) => {
    store.commit('handleJobUpdate', update)
})

export default store
