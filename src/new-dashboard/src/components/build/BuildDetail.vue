<template>
    <div v-if="data">
		<md-card class="example-box">
            <md-card-header>
                <md-card-header-text>
                    <div class="md-title">
                       <h3 class="md-title">
                            <router-link :to="{name: 'ProjectDetail', params: {
                                projectName: data.project.name
                            }}">
                                {{ data.project.name }}
                            </router-link>
                            / Build {{ data.build.number }}.{{ data.build.restartCounter }}
                        </h3>
                    </div>
                </md-card-header-text>
                <md-toolbar class="md-dense">
                    <md-button class="md-raised" v-on:click="data.build.abort()">Abort</md-button>
                    <md-button class="md-raised" v-on:click="data.build.restart()">Restart</md-button>
                    <md-button class="md-raised" v-on:click="data.build.clearCache()">Clear Cache</md-button>
                </md-toolbar>
            </md-card-header>
		</md-card>

        <md-layout md-gutter>
            <md-layout md-flex-xsmall="100" md-flex-small="75" md-flex-medium="75" md-flex-large="75">
                <md-card class="example-box">
                    <md-table-card>
                        <md-card-area>
                            <!--<ib-job-gantt :jobs="data.build.jobs"></ib-job-gantt>-->
                        </md-card-area>
                    </md-table-card>
                </md-card>
            </md-layout>

            <md-layout md-flex-xsmall="100" md-flex-small="25" md-flex-medium="25" md-flex-large="25">
                <md-card class="example-box">
                    <ib-state-big :state="data.build.state"></ib-state-big>
              <md-list class="md-dense">
                <md-list-item>
                    <md-icon>move_to_inbox</md-icon>
                    <span>
                        <ib-date :date="data.build.startDate"></ib-date>
                    </span>
                </md-list-item>

                <md-list-item>
                  <md-icon>send</md-icon>
                  <span>
                      <ib-duration :start="data.build.startDate" :end="data.build.endDate">
                      </ib-duration>
                  </span>
                </md-list-item>

                <md-list-item>
                    <md-icon>delete</md-icon>
                    <span><ib-commit-sha :sha="data.build.commit.id"></ib-commit-sha></span>
                </md-list-item>

                <md-list-item>
                    <md-icon>error</md-icon> <span>{{ data.build.commit.author_name }}</span>
                </md-list-item>

                <md-list-item>
                    <md-icon>error</md-icon> <span>{{ data.build.commit.branch }}</span>
                </md-list-item>
              </md-list>

                </md-card>
            </md-layout>
       </md-layout>
    </div>
</template>

<script>
import store from '../../store'
import ProjectService from '../../services/ProjectService'
import GanttChart from './Gantt'
import StateBig from '../utils/StateBig'
import Date from '../utils/Date'
import Duration from '../utils/Duration'
import CommitSha from '../utils/CommitSha'

export default {
    name: 'BuildDetail',
    props: ['projectName', 'buildNumber', 'buildRestartCounter'],
    components: {
        'ib-job-gantt': GanttChart,
        'ib-state-big': StateBig,
        'ib-date': Date,
        'ib-duration': Duration,
        'ib-commit-sha': CommitSha
    },
    store,
    asyncComputed: {
        data: {
            get () {
                let project = null
                return ProjectService
                    .findProjectByName(this.projectName)
                    .then((p) => {
                        project = p
                        return p.getBuild(this.buildNumber, this.buildRestartCounter)
                    })
                    .then((build) => {
                        build._updateState()
                        return {
                            project,
                            build
                        }
                    })
            },
            watch () {
                // eslint-disable-next-line no-unused-expressions
                this.projectName
                // eslint-disable-next-line no-unused-expressions
                this.buildNumber
                // eslint-disable-next-line no-unused-expressions
                this.buildRestartCounter
            }
        }
    }
}
</script>

<style scoped>
  .example-box {
    margin-top: 16px;
    margin-left: 16px;
    margin-right: 16px;
    width: 98%;
  }
  .md-title {
    position: relative;
    z-index: 3;
  }
</style>

