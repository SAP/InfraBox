<template>
    <div class="m-sm full-height">
        <md-card md-theme="white" class="full-height clean-card">
            <md-card-header>
                <md-card-header-text class="setting-list">
                    <md-icon>security</md-icon>
                    <span>Badges</span>
                </md-card-header-text>
            </md-card-header>

            <md-card-area>
                <md-list class="m-b-md">
                    <md-list-item class="m-r-xl">
                        <div>
                            <img :src="buildState" />
                            <pre>[![Build Status]({{ root_url }}/api/v1/projects/{{ project.id }}/state.svg)]({{ root_url }}/dashboard/#/project/{{ project.name }})</pre>
                        </div>
                    </md-list-item>
                    <md-list-item class="m-r-xl">
                        <div>
                            <img :src="testState" />
                            <pre>[![Test Status]({{ root_url }}/api/v1/projects/{{ project.id }}/tests.svg)]({{ root_url }}/dashboard/#/project/{{ project.name }})</pre>
                        </div>
                    </md-list-item>
                </md-list>
            </md-card-area>
        </md-card>
    </div>
</template>

<script>
import store from '../../store'

export default {
    props: ['project'],
    created () {
        this.root_url = store.state.settings.INFRABOX_ROOT_URL
        this.buildState = `${this.root_url}/api/v1/projects/${this.project.id}/state.svg`
        this.testState = `${this.root_url}/api/v1/projects/${this.project.id}/tests.svg`
    }
}
</script>
