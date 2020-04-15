import Vue from 'vue'
import Router from 'vue-router'
import Overview from '@/components/Overview'
import AddProject from '@/components/AddProject'
import Login from '@/components/account/Login'
import Signup from '@/components/account/Signup'
import ProjectDetailBuilds from '@/components/project/ProjectDetailBuilds'
import ProjectDetailSettings from '@/components/project/ProjectDetailSettings'
import TriggerBuild from '@/components/project/Trigger'
import BuildDetailGraph from '@/components/build/BuildDetailGraph'
import BuildDetailJobs from '@/components/build/BuildDetailJobs'
import JobDetail from '@/components/job/JobDetail'
import TestDetail from '@/components/test/TestDetail'
import AdminUsers from '@/components/admin/AdminUsers'
import AdminProjects from '@/components/admin/AdminProjects'
import AdminClusters from '@/components/admin/AdminClusters'

import UserService from '../services/UserService'

Vue.use(Router)

let loginGuard = function (to, from, next) {
    if (process.env.NODE_ENV === 'development') {
        next()
    } else {
        if (UserService.isLoggedIn()) {
            next()
        } else {
            next('/login')
        }
    }
}

export default new Router({
    routes: [{
        path: '/',
        name: 'Overview',
        component: Overview,
        beforeEnter: loginGuard
    }, {
        path: '/addproject',
        name: 'addproject',
        component: AddProject,
        beforeEnter: loginGuard
    }, {
        path: '/login',
        name: 'login',
        component: Login,
        beforeEnter (to, from, next) {
            if (UserService.isLoggedIn()) {
                next('/')
            } else {
                next()
            }
        }
    }, {
        path: '/signup',
        name: 'signup',
        component: Signup
    }, {
        path: '/admin/projects',
        name: 'AdminProjects',
        component: AdminProjects,
        beforeEnter: loginGuard
    }, {
        path: '/admin/users',
        name: 'AdminUsers',
        component: AdminUsers,
        beforeEnter: loginGuard
    }, {
        path: '/admin/clusters',
        name: 'AdminClusters',
        component: AdminClusters,
        beforeEnter: loginGuard
    }, {
        path: '/project/:projectName',
        name: 'ProjectDetailBuilds',
        component: ProjectDetailBuilds,
        props: true
    }, {
        path: '/project/:projectName/settings',
        name: 'ProjectDetailSettings',
        component: ProjectDetailSettings,
        props: true,
        beforeEnter: loginGuard
    }, {
        path: '/project/:projectName/trigger',
        name: 'TriggerBuild',
        component: TriggerBuild,
        props: true,
        beforeEnter: loginGuard
    }, {
        path: '/project/:projectName/build/:buildNumber/:buildRestartCounter',
        name: 'BuildDetailGraph',
        component: BuildDetailGraph,
        props: function (route) {
            return {
                projectName: route.params.projectName,
                buildNumber: parseInt(route.params.buildNumber),
                buildRestartCounter: parseInt(route.params.buildRestartCounter)
            }
        }
    }, {
        path: '/project/:projectName/build/:buildNumber/:buildRestartCounter/jobs',
        name: 'BuildDetailJobs',
        component: BuildDetailJobs,
        props: function (route) {
            return {
                projectName: route.params.projectName,
                buildNumber: parseInt(route.params.buildNumber),
                buildRestartCounter: parseInt(route.params.buildRestartCounter)
            }
        }
    }, {
        path: '/project/:projectName/build/:buildNumber/:buildRestartCounter/job/:jobName',
        name: 'JobDetail',
        component: JobDetail,
        props: function (route) {
            return {
                projectName: route.params.projectName,
                buildNumber: parseInt(route.params.buildNumber),
                buildRestartCounter: parseInt(route.params.buildRestartCounter),
                jobName: route.params.jobName
            }
        }
    }, {
        path: '/project/:projectName/build/:buildNumber/:buildRestartCounter/job/:jobName/suite/:suiteName/test/:testName',
        name: 'TestDetail',
        component: TestDetail,
        props: function (route) {
            return {
                projectName: route.params.projectName,
                buildNumber: parseInt(route.params.buildNumber),
                buildRestartCounter: parseInt(route.params.buildRestartCounter),
                jobName: route.params.jobName,
                suiteName: route.params.suiteName,
                testName: route.params.testName
            }
        }
    }]
})
