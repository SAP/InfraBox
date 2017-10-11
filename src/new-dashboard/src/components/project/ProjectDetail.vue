<template>
<md-card>
<md-card-header>
    <md-card-header-text>
      <div class="md-title">Title goes here</div>
      <div class="md-subhead">Subtitle here</div>
    </md-card-header-text>

    <md-menu md-size="4" md-direction="bottom left">
      <md-button class="md-icon-button" md-menu-trigger>
        <md-icon>more_vert</md-icon>
      </md-button>

      <md-menu-content>
        <md-menu-item>
          <span>Call</span>
          <md-icon>phone</md-icon>
        </md-menu-item>

        <md-menu-item>
          <span>Send a message</span>
          <md-icon>message</md-icon>
        </md-menu-item>
      </md-menu-content>
    </md-menu>

</md-card-header>
<md-card-content>
  <md-table v-if="project">
	  <md-table-header>
		<md-table-row>
		  <md-table-head>Build</md-table-head>
		  <md-table-head v-if="project.isGit()">Author</md-table-head>
		  <md-table-head v-if="project.isGit()">Branch</md-table-head>
		  <md-table-head>Start Time</md-table-head>
		  <md-table-head>Duration</md-table-head>
		  <md-table-head v-if="project.isGit()">Type</md-table-head>
		</md-table-row>
	  </md-table-header>

	  <md-table-body>
		<md-table-row v-for="b in project.builds" :key="b.id">
		  <md-table-cell><ib-state :state="b.state"></ib-state>
			{{ b.number }}.{{ b.restartCounter }}</md-table-cell>
          <md-table-cell v-if="project.isGit()">{{ b.commit.author_name }}</md-table-cell>
          <md-table-cell v-if="project.isGit()">{{ b.commit.branch }}</md-table-cell>
          <md-table-cell><ib-date :date="b.start_date"></ib-date></md-table-cell>
          <md-table-cell><ib-duration :start="b.start_date" :end="b.end_date"></ib-duration></md-table-cell>
          <md-table-cell v-if="project.isGit()"><ib-gitjobtype :build="b"></ib-gitjobtype></md-table-cell>
		</md-table-row>
	  </md-table-body>
	</md-table>
</md-card-content>
</md-card>
</template>

<script>
import store from '../../store'
import ProjectService from '../../services/ProjectService'

export default {
    name: 'ProjectDetail',
    props: ['projectName'],
    store,
    asyncComputed: {
        project: {
            get () {
                return ProjectService
                    .findProjectByName(this.projectName)
            },
            watch () {
                // eslint-disable-next-line no-unused-expressions
                this.projectName
            }
        }
    }
}
</script>
