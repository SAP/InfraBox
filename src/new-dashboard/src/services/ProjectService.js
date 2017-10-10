import Vue from 'vue'

import store from '../store'
import events from '../events'

class ProjectService {
  init () {
    this.loaded = this._loadProjects()
  }

  findProjectByName (name) {
    return this.loaded.then(() => {
      return this._findProjectByName(name)
    })
  }

  _findProjectByName (name) {
    for (let p of store.state.projects) {
      if (p.name === name) {
        return new Promise((resolve) => { resolve(p) })
      }
    }

    return new Promise((resolve, reject) => { reject(new Error('Project not found')) })
  }

  _loadProjects () {
    return Vue.http.get('http://localhost:3000/api/dashboard/project').then((response) => {
      for (let p of response.body) {
        store.commit('addProject', p)
        events.listenJobs(p)
      }
    })
  }
}

export default new ProjectService()
