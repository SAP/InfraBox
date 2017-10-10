// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
import Vue from 'vue'
import VueResource from 'vue-resource'
import VueMaterial from 'vue-material'
import { sync } from 'vuex-router-sync'
import AsyncComputed from 'vue-async-computed'

import App from './App'
import router from './router'
import store from './store'
import ProjectService from './services/ProjectService'

import 'vue-material/dist/vue-material.css'

sync(store, router)

Vue.config.productionTip = false
Vue.use(VueResource)
Vue.use(VueMaterial)
Vue.use(AsyncComputed)

ProjectService.init()

/* eslint-disable no-new */
new Vue({
  el: '#app',
  router,
  store,
  template: '<App/>',
  components: { App }
})
