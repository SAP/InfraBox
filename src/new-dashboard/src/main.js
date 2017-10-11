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
import 'font-awesome/css/font-awesome.css'

import NotificationComponent from '@/components/Notification'
import StateComponent from '@/components/utils/State'
import DateComponent from '@/components/utils/Date'
import ProjectDetailComponent from '@/components/project/ProjectDetail'
import DurationComponent from '@/components/utils/Duration'
import GitJobTypeComponent from '@/components/utils/GitJobType'
import NotificationService from './services/NotificationService'
import Notification from './models/Notification'

sync(store, router)

Vue.config.productionTip = false
Vue.use(VueResource)
Vue.use(VueMaterial)
Vue.use(AsyncComputed, {
    useRawError: true,
    errorHandler (err) {
        console.error(err)
        let message = 'Internal Error occured'
        if (err.body && err.body.message) {
            message = err.body.message
        }

        NotificationService.$emit('NOTIFICATION', new Notification(message))
    }
})

ProjectService.init()

Vue.component('ib-notifications', NotificationComponent)
Vue.component('ib-state', StateComponent)
Vue.component('ib-date', DateComponent)
Vue.component('ib-duration', DurationComponent)
Vue.component('ib-gitjobtype', GitJobTypeComponent)
Vue.component('ib-project', ProjectDetailComponent)

/* eslint-disable no-new */
new Vue({
    el: '#app',
    router,
    store,
    template: '<App/>',
    components: {
        App
    }
})
