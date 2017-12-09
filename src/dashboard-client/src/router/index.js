import Vue from 'vue'
import Router from 'vue-router'
import Overview from '@/components/Overview'
import AddProject from '@/components/AddProject'
import Login from '@/components/account/Login'
import Signup from '@/components/account/Signup'
import ProjectDetail from '@/components/project/ProjectDetail'
import TriggerBuild from '@/components/project/Trigger'
import BuildDetail from '@/components/build/BuildDetail'
import JobDetail from '@/components/job/JobDetail'

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
        name: 'ProjectDetail',
        component: ProjectDetail,
        props: true
    }, {
        path: '/project/:projectName/trigger',
        name: 'TriggerBuild',
        component: TriggerBuild,
        props: true
    }, {
        path: '/project/:projectName/build/:buildNumber/:buildRestartCounter',
        name: 'BuildDetail',
        component: BuildDetail,
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
    }]
})
