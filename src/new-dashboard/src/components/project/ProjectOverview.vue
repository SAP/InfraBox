<template>
    <div v-if="project">
        <md-card-header>
            <md-card-header-text>
                <div class="md-title">
                    <span v-if="project.isGit()"><i class="fa fa-github"></i></span>
                    <span v-if="!project.isGit()"><i class="fa fa-home"></i></span>
                    <router-link :to="{name: 'ProjectDetail', params: {projectName: project.name}}" class="m-l-xs">{{ project.name }}</router-link>
                </div>
            </md-card-header-text>
            <md-menu md-size="4" md-direction="bottom left">
                <md-button class="md-icon-button md-accent" md-menu-trigger>
                    <md-icon>more_vert</md-icon>
                </md-button>

                <md-menu-content>
                    <md-menu-item>
                        <span>Edit</span>
                        <md-icon>mode_edit</md-icon>
                    </md-menu-item>
                    <md-menu-item>
                        <span>Cancel Build</span>
                        <md-icon>cancel</md-icon>
                    </md-menu-item>
                    <md-menu-item>
                        <span>Restart Build</span>
                        <md-icon>replay</md-icon>
                    </md-menu-item>
                    <md-menu-item>
                        <span>Clear Cache</span>
                        <md-icon>delete_sweep</md-icon>
                    </md-menu-item>
                </md-menu-content>
            </md-menu>
        </md-card-header>
        <md-card-content>
            <md-table>
                <md-table-body v-if="project.builds.length != 0">
                    <md-table-row>
                        <md-table-cell class="md-body-2"><i class="fa fa-circle-thin"></i><span style="padding-left: 16px">State</span></md-table-cell>
                        <md-table-cell><ib-state :state="project.builds[0].state" look="small"></ib-state></md-table-cell>
                    </md-table-row>
                    <md-table-row>
                        <md-table-cell class="md-body-2"><i class="fa fa-cube"></i><span style="padding-left: 16px">Build</span></md-table-cell>
                        <md-table-cell>
                            {{ project.builds[0].number }}.{{ project.builds[0].restartCounter }}
                        </md-table-cell>
                    </md-table-row>
                    <md-table-row v-if="project.isGit()">
                        <md-table-cell class="md-body-2"><i class="fa fa-user"></i><span style="padding-left: 16px">Author</span></md-table-cell>
                        <md-table-cell v-if="project.isGit()">
                            {{ project.builds[0].commit.author_name }}
                        </md-table-cell>
                    </md-table-row>
                    <md-table-row v-if="project.isGit()">
                        <md-table-cell class="md-body-2"><i class="fa fa-code-fork"></i><span style="padding-left: 16px">Branch</span></md-table-cell>
                        <md-table-cell v-if="project.isGit()">
                            {{ project.builds[0].commit.branch }}
                        </md-table-cell>
                    </md-table-row>
                    <md-table-row>
                        <md-table-cell class="md-body-2"><i class="fa fa-calendar"></i><span style="padding-left: 16px"> Started</span></md-table-cell>
                        <md-table-cell><ib-date :date="project.builds[0].start_date"></ib-date></md-table-cell>
                    </md-table-row>
                    <md-table-row>
                        <md-table-cell class="md-body-2"><i class="fa fa-clock-o"></i><span style="padding-left: 16px">Duration</span></md-table-cell>
                        <md-table-cell>
                            <ib-duration :start="project.builds[0].start_date" :end="project.builds[0].end_date"></ib-duration>
                        </md-table-cell>
                    </md-table-row>
                    <md-table-row v-if="project.isGit()">
                        <md-table-cell class="md-body-2"><i class="fa fa-file"></i><span style="padding-left: 16px">Type</span></md-table-cell>
                        <md-table-cell v-if="project.isGit()">
                            <ib-gitjobtype :build="project.builds[0]"></ib-gitjobtype>
                        </md-table-cell>
                    </md-table-row>
                </md-table-body>
            </md-table>
        </md-card-content>
    </div>
</template>

<script>
import BuildTable from '../build/BuildTable'

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

</style>
