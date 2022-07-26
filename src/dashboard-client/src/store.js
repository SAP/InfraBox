import Vue from 'vue'
import Vuex from 'vuex'
import events from './events'
import _ from 'underscore'

import Project from './models/Project'
import Build from './models/Build'
import Job from './models/Job'
import Test from './models/Test'

Vue.use(Vuex)

const state = {
    user: null,
    projects: [],
    jobs: {},
    settings: {},
    admin: {
        projects: [],
        users: [],
        clusters: []
    }
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

function toDate (s) {
    let a = s.split(/[^0-9]/)
    let dateStr = a[0] + '-' + a[1] + '-' + a[2] + 'T' + a[3] + ':' + a[4] + 'Z'

    return new Date(dateStr)
}

function handleJobUpdate (state, event) {
    const project = findProject(state, event.data.project.id)

    let commit = null

    if (project.isGit() && event.data.commit) {
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
        build = new Build(
            event.data.build.id,
            event.data.build.build_number,
            event.data.build.restart_counter,
            event.data.build.is_cronjob,
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
    const d = event.data.job

    let startDate = null
    let endDate = null

    if (d.start_date) {
        startDate = toDate(d.start_date)
    }

    if (d.end_date) {
        endDate = toDate(d.end_date)
    }

    if (!job) {
        const job = new Job(
            d.id,
            d.name,
            d.state,
            startDate,
            endDate,
            build,
            project,
            d.dependencies,
            d.message,
            d.definition,
            d.node_name,
            d.avg_cpu,
            d.restarted
        )

        let jobs = build.jobs
        jobs.push(job)
        jobs = _.sortBy(jobs, (j) => { return j.name })

        build.jobs = jobs
        state.jobs[d.id] = job
    } else {
        job.name = d.name
        job.state = d.state
        job.startDate = startDate
        job.endDate = endDate
        job.nodeName = d.node_name
        job.avgCpu = d.avg_cpu
        job.restarted = d.restarted
        job.dependencies = d.dependencies || []

        if (d.message) {
            job.message = d.message
        }
    }

    build._updateState()
    project._updateState()
}

function addProjects (state, projects) {
    for (const project of projects) {
        let p = findProject(state, project.id)
        if (p) {
            continue
        }

        p = new Project(project.name, project.id, project.type, project.userrole, project.public)
        state.projects.push(p)

        state.projects = _.sortBy(state.projects, function (i) { return i.name.toLowerCase() })

        p._loadJobs()
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

function setSSHKeys (state, data) {
    const project = data.project
    const sshkeys = data.sshkeys
    project.sshkeys = sshkeys
}

function setCronJobs (state, data) {
    const project = data.project
    const cronjobs = data.cronjobs
    project.cronjobs = cronjobs
}

function setSecrets (state, data) {
    const project = data.project
    const secrets = data.secrets
    project.secrets = secrets
}

function setVault (state, data) {
    const project = data.project
    const vault = data.vault
    project.vault = vault
}

function setPattern (state, data) {
    const project = data.project
    const pattern = data.pattern
    project.pattern = pattern
}

function setCollaborators (state, data) {
    const project = data.project
    const collaborators = data.collaborators
    project.collaborators = collaborators
}

function setRoles (state, data) {
    const project = data.project
    const roles = data.roles
    project.roles = roles
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
}

function setSettings (state, settings) {
    state.settings = settings
}

function setBadges (state, data) {
    const job = data.job
    const badges = data.badges
    job.badges = badges
}

function setTests (state, data) {
    const job = data.job
    const t = []

    for (const test of data.tests) {
        t.push(new Test(test, job))
    }

    job.tests = t
}

function setStats (state, data) {
    const job = data.job
    const stats = data.stats
    job.stats = stats
}

function setArchive (state, data) {
    const job = data.job
    const archive = data.archive
    job.archive = archive
}

function setTabs (state, data) {
    const job = data.job
    const tabs = data.tabs
    job.tabs = tabs
}

function handleConsoleUpdate (state, update) {
    const job = state.jobs[update.job_id]
    if (!job) {
        return
    }

    if (!update.data) {
        return
    }

    const lines = update.data.split('\n')
    job._addLines(lines)
}

function setConsole (state, data) {
    const job = data.job
    const console = data.console
    const lines = console.split('\n')
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

function setAdminUsers (state, users) {
    state.admin.users = users
}

function setAdminProjects (state, projects) {
    state.admin.projects = projects
}

function setAdminClusters (state, clusters) {
    state.admin.clusters = clusters
}

function updateAdminCluster (state, payload) {
    const { name, enabled } = payload
    const cluster = state.admin.clusters.find(c => c.name === name)
    cluster.enabled = enabled
}

function setAdminUserRole (state, payload) {
    const { id, role } = payload
    const user = state.admin.users.find(c => c.id === id)
    user.role = role
}

const mutations = {
    addProjects,
    addJobs,
    setSecrets,
    setCronJobs,
    setSSHKeys,
    setCollaborators,
    setRoles,
    setTokens,
    handleJobUpdate,
    setUser,
    setGithubRepos,
    handleConsoleUpdate,
    deleteProject,
    setSettings,
    setBadges,
    setConsole,
    setTests,
    setStats,
    setTabs,
    setAdminUsers,
    setAdminUserRole,
    setAdminProjects,
    setAdminClusters,
    updateAdminCluster,
    setArchive,
    setVault,
    setPattern
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
