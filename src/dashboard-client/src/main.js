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

import 'vue-material/dist/vue-material.css'
import 'font-awesome/css/font-awesome.css'
import '../static/css/infrabox.css'
import 'taucharts/build/production/tauCharts.default.min.css'

import NotificationComponent from '@/components/Notification'
import StateComponent from '@/components/utils/State'
import DateComponent from '@/components/utils/Date'
import ProjectOverviewComponent from '@/components/project/ProjectOverview'
import DurationComponent from '@/components/utils/Duration'
import GitJobTypeComponent from '@/components/utils/GitJobType'
import UserService from './services/UserService'
import NotificationService from './services/NotificationService'
import Notification from './models/Notification'

require('../static/git-commit.svg')

sync(store, router)

Vue.config.productionTip = false
Vue.use(VueResource)
Vue.use(VueMaterial)
Vue.use(AsyncComputed, {
    useRawError: true,
    errorHandler (err) {
        NotificationService.$emit('NOTIFICATION', new Notification(err))
    }
})

UserService.init()

Vue.component('ib-notifications', NotificationComponent)
Vue.component('ib-state', StateComponent)
Vue.component('ib-date', DateComponent)
Vue.component('ib-duration', DurationComponent)
Vue.component('ib-gitjobtype', GitJobTypeComponent)
Vue.component('ib-overview', ProjectOverviewComponent)

Vue.material.registerTheme({
    default: {
        primary: {
            color: 'blue-grey',
            hue: 900,
            textColor: 'white'
        },
        accent: {
            color: 'cyan',
            hue: 600,
            textColor: 'white'
        },
        warn: {
            color: 'red',
            hue: 900,
            textColor: 'white'
        },
        background: {
            color: 'grey',
            hue: 100,
            textColor: 'black'
        }
    },
    error: {
        primary: {
            color: 'black',
            hue: '900',
            textColor: 'white'
        },
        accent: {
            color: 'grey',
            hue: 100,
            textColor: 'black'
        }
    },
    failure: {
        primary: {
            color: 'red',
            hue: '900',
            textColor: 'white'
        },
        accent: {
            color: 'red',
            hue: 100,
            textColor: 'grey'
        }
    },
    unstable: {
        primary: {
            color: 'red',
            hue: '900',
            textColor: 'white'
        },
        accent: {
            color: 'red',
            hue: 100,
            textColor: 'grey'
        }
    },
    finished: {
        primary: {
            color: 'green',
            hue: '600',
            textColor: 'white'
        },
        accent: {
            color: 'green',
            hue: 100,
            textColor: 'grey'
        }
    },
    killed: {
        primary: {
            color: 'grey',
            hue: '700',
            textColor: 'white'
        },
        accent: {
            color: 'grey',
            hue: 100,
            textColor: 'grey'
        }
    },
    queued: {
        primary: {
            color: 'grey',
            hue: 500,
            textColor: 'white'
        },
        accent: {
            color: 'cyan',
            hue: 100,
            textColor: 'grey'
        }
    },
    running: {
        primary: {
            color: 'cyan',
            hue: 600,
            textColor: 'white'
        },
        accent: {
            color: 'cyan',
            hue: 100,
            textColor: 'grey'
        }
    },
    scheduled: {
        primary: {
            color: 'grey',
            hue: 300,
            textColor: 'black'
        },
        accent: {
            color: 'cyan',
            hue: 100,
            textColor: 'grey'
        }
    },
    skipped: {
        primary: {
            color: 'grey',
            hue: 400,
            textColor: 'white'
        },
        accent: {
            color: 'cyan',
            hue: 100,
            textColor: 'grey'
        }
    }
})

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
