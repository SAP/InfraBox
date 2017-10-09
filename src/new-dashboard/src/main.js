// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
import Vue from 'vue'
import VueResource from 'vue-resource'
import VueMaterial from 'vue-material'
import VueSocketio from 'vue-socket.io'

import App from './App'
import router from './router'
import store from './store'

import 'vue-material/dist/vue-material.css'

Vue.config.productionTip = false
Vue.use(VueSocketio, 'ws://localhost:3000', store)
Vue.use(VueResource)
Vue.use(VueMaterial)

/* eslint-disable no-new */
new Vue({
  el: '#app',
  router,
  store,
  template: '<App/>',
  components: { App }
})
