<template>
    <md-list md-theme="white">
        <md-list-item class="white-bg">
            <md-icon>security</md-icon>
            <span>Badges</span>

            <md-list-expand>
                <md-list class="m-b-md">
                    <md-list-item class="md-inset m-r-xl">
                        <div>
                            <img :src="buildState" />
                            <pre>[![Build Status]({{ api_host }}/v1/project/{{ project.id }}/build/state.svg)]({{ dashboard_host }}/dashboard/#/project/{{ project.name }})</pre>
                        </div>
                    </md-list-item>
                    <md-list-item class="md-inset m-r-xl">
                        <div>
                            <img :src="testState" />
                            <pre>[![Test Status]({{ api_host }}/v1/project/{{ project.id }}/build/tests.svg)]({{ dashboard_host }}/dashboard/#/project/{{ project.name }})</pre>
                        </div>
                    </md-list-item>
                </md-list>
            </md-list-expand>
        </md-list-item>
    </md-list>
</template>

<script>
import store from '../../store'

export default {
    props: ['project'],
    created () {
        this.api_host = store.state.settings.INFRABOX_API_URL
        this.dashboard_host = store.state.settings.INFRABOX_DASHBOARD_URL
        this.buildState = `${this.api_host}/v1/project/${this.project.id}/build/state.svg`
        this.testState = `${this.api_host}/v1/project/${this.project.id}/build/tests.svg`
    }
}
</script>
