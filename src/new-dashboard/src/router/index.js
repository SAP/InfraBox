import Vue from 'vue'
import Router from 'vue-router'
import Overview from '@/components/Overview'
import ProjectDetail from '@/components/project/ProjectDetail'
import BuildDetail from '@/components/build/BuildDetail'

Vue.use(Router)

export default new Router({
    routes: [{
        path: '/',
        name: 'Overview',
        component: Overview
    }, {
        path: '/project/:projectName',
        name: 'ProjectDetail',
        component: ProjectDetail,
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
    }]
})
