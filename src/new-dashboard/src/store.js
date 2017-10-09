import Vue from 'vue'
import Vuex from 'vuex'

Vue.use(Vuex)

function getCookie (cname) {
  const name = cname + '='
  const ca = document.cookie.split(';')
  for (let c of ca) {
    while (c.charAt(0) === ' ') {
      c = c.substring(1)
    }

    if (c.indexOf(name) === 0) {
      return c.substring(name.length, c.length)
    }
  }
  return ''
}

export function getToken () {
  return getCookie('token')
}

const state = {
  projects: []
}

const mutations = {
  addProject (state, project) {
    state.projects.push(project)
  },
  SOCKET_CONNECT (state, status) {
    console.log('status', status)
  },
  SOCKET_USER_MESSAGE (state, message) {
    console.log('message', message)
  }
}

const actions = {
  loadProjects (context) {
    Vue.http.get('http://localhost:3000/api/dashboard/project').then(response => {

      for (let p of response.body) {
        context.commit('addProject', p)
        //Vue.socket.emit('listen:jobs', p.id)
      }
    }, response => {
      console.log(response)
    })
  }
}

export default new Vuex.Store({
  state,
  actions,
  mutations
})
