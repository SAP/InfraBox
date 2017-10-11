<template>
    <div class="example-box">
		<md-card v-if="project" class="example-box-card">
			<md-toolbar md-theme="white" class="md-dense">
				<h3 class="md-title">{{ project.name }}</h3>
			</md-toolbar>

			  <md-card-area>
				<md-tabs md-right :md-dynamic-height="false" class="md-transparent example-tabs">


  <template slot="header-item" scope="props">
    <md-icon v-if="props.header.icon">{{ props.header.icon }}</md-icon>
    <template v-if="props.header.options && props.header.options.new_badge">
      <span v-if="props.header.label" class="label-with-new-badge">
        {{ props.header.label }}
        <span class="new-badge">{{ props.header.options.new_badge }}</span>
      </span>
    </template>
    <template v-else>
      <span v-if="props.header.label">{{ props.header.label }}</span>
    </template>
  </template>


				  <md-tab class="example-content" md-label="Builds" md-icon="search" :md-options="{new_badge: 1}" md-active>
					<slot name="demo">
                       <ib-build-table :project="project"></ib-build-table>
                    </slot>
				  </md-tab>

				  <md-tab class="code-content" md-label="Settings" md-icon="phone">
					<slot name="code">
                        Settings
                    </slot>
				  </md-tab>
				</md-tabs>
			  </md-card-area>
		</md-card>
    </div>
</template>

<script>
/*
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
*/

import BuildTable from './BuildTable'

export default {
    props: ['project'],
    components: {
        'ib-build-table': BuildTable
    }
}
</script>

<style scoped>
  .example-box {
    margin: 16px;
  }
  .md-title {
    position: relative;
    z-index: 3;
  }
  .example-tabs {
    margin-top: -48px;
    @media (max-width: 480px) {
      margin-top: -1px;
      background-color: #fff;
    }
  }
.label-with-new-badge{font-weight:bolder}.new-badge{background-color:red;color:#fff;padding:3px;border-radius:3px}
</style>

