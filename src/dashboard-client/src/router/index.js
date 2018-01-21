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

Vue.use(Router)

export default new Router({
    routes: [{
        path: '/',
        name: 'Overview',
        component: Overview
    }, {
        path: '/addproject',
        name: 'addproject',
        component: AddProject
    }, {
        path: '/login',
        name: 'login',
        component: Login
    }, {
        path: '/signup',
        name: 'signup',
        component: Signup
    }, {
        path: '/project/:projectName',
        name: 'ProjectDetailBuilds',
        component: ProjectDetailBuilds,
        props: true
    }, {
        path: '/project/:projectName/settings',
        name: 'ProjectDetailSettings',
        component: ProjectDetailSettings,
        props: true
    }, {
        path: '/project/:projectName/trigger',
        name: 'TriggerBuild',
        component: TriggerBuild,
        props: true
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
