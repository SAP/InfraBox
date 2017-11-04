import Vue from 'vue'
import Vuex from 'vuex'
import events from './events'
import _ from 'underscore'

import Project from './models/Project'
import Build from './models/Build'
import Job from './models/Job'

Vue.use(Vuex)

const state = {
    user: null,
    projects: [],
    jobs: {}
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
        job.endDate = new Date(j.end_date)

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
                              commit, event.data.pull_request,
                              project)

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
            let startDate = null

            if (d.start_date) {
                startDate = new Date(d.start_date)
            }

            const job = new Job(
                d.id,
                d.name,
                d.cpu,
                d.memory,
                d.state,
                startDate,
                new Date(d.end_date),
                build,
                project,
                d.dependencies
            )
            build.jobs.push(job)
            state.jobs[d.id] = job
        }

        build._updateState()
        updateProjectState(project)
    }
}

function setProjects (state, projects) {
    for (const project of projects) {
        const p = findProject(state, project.id)
        if (p) {
            continue
        }

        state.projects.push(new Project(project.name, project.id, project.type))
        events.listenJobs(project)
    }
}

function addJobs (state, jobs) {
    for (const job of jobs) {
        handleJobUpdate(state, {
            type: 'INSERT',
            data: job
        })
    }
}

function setSecrets (state, data) {
    const project = data.project
    const secrets = data.secrets
    project.secrets = secrets
}

function setCollaborators (state, data) {
    const project = data.project
    const collaborators = data.collaborators
    project.collaborators = collaborators
}

function setTokens (state, data) {
    const project = data.project
    const tokens = data.tokens
    project.tokens = tokens
}

function setUser (state, user) {
    state.user = user
}

function setGithubRepos (state, repos) {
    state.user.githubRepos = repos
    console.log(repos)
}

function handleConsoleUpdate (state, update) {
    const job = state.jobs[update.job_id]
    if (!job) {
        return
    }

    const lines = update.data.split('\n')
    job._addLines(lines)
}

function deleteProject (state, projectId) {
    let i = 0
    for (; i < state.projects.length; ++i) {
        const p = state.projects[i]
        if (p.id === projectId) {
            state.projects.splice(i, 1)
            break
        }
    }
}

const mutations = {
    setProjects,
    addJobs,
    setSecrets,
    setCollaborators,
    setTokens,
    handleJobUpdate,
    setUser,
    setGithubRepos,
    handleConsoleUpdate,
    deleteProject
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

events.$on('NOTIFY_CONSOLE', (update) => {
    store.commit('handleConsoleUpdate', update)
})

export default store
