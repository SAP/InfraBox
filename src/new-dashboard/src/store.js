import Vue from 'vue'
import Vuex from 'vuex'
import events from './events'
import _ from 'underscore'

Vue.use(Vuex)

class Build {
  constructor (id, number, restartCounter) {
    this.id = id
    this.number = number
    this.restartCounter = restartCounter
    this.state = 'running'
    this.jobs = []
  }
}

class Project {
  constructor (name, id) {
    this.name = name
    this.id = id
    this.builds = []
    this.commits = []
    this.state = 'finished'
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
}

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

function updateBuildState (build) {
  build.state = 'finished'

  for (let j of build.jobs) {
    if (j.state === 'queued' || j.state === 'scheduled' || j.state === 'running') {
      build.state = 'running'
      return
    }

    if (j.state === 'error' || j.state === 'failure' || j.state === 'killed') {
      build.state = 'failure'
    }
  }
}

function handleJobUpdate (state, event) {
  if (event.type === 'UPDATE') {
    const project = findProject(state, event.data.project.id)
    const build = findBuild(project, event.data.build.id)
    const job = findJob(build, event.data.job.id)

    const j = event.data.job
    job.state = j.state
    job.end_date = j.end_date

    updateBuildState(build)
    updateProjectState(project)
  } else if (event.type === 'INSERT') {
    const project = findProject(state, event.data.project.id)

    // Update Build
    let build = findBuild(project, event.data.build.id)
    if (!build) {
      build = new Build(event.data.build.id,
                        event.data.build.build_number,
                        event.data.build.restart_counter)

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

    // Update Commit
    if (event.data.commit) {
      let commit = findCommit(project, event.data.commit.id)
      if (!commit) {
        commit = event.data.commit
        project.commits.push(commit)
      }
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
        start_date: d.start_date,
        end_date: d.end_date
      }
      build.jobs.push(job)
    }

    updateBuildState(build)
    updateProjectState(project)
  }
}

function addProject (state, project) {
  state.projects.push(new Project(project.name, project.id))
}

function findProjectByNameParam (state) {
  for (let p of state.projects) {
    if (p.name === state.route.params.projectName) {
      return p
    }
  }

  return null
}

const getters = {
  findProjectByNameParam
}

const mutations = {
  addProject,
  handleJobUpdate
}

const actions = {
  loadProjects (context) {
    Vue.http.get('http://localhost:3000/api/dashboard/project').then(response => {
      for (let p of response.body) {
        context.commit('addProject', p)
        events.listenJobs(p)
      }
    }, response => {
      console.log(response)
    })
  }
}

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
