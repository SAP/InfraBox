<template>
    <md-list-item class="setting-list">
        <md-icon>security</md-icon>
        <span>Badges</span>

        <md-list-expand>
            <md-list class="m-t-md m-b-md">
                <md-list-item class="md-inset m-r-xl">
                    <div>
                        <img :src="api_host + '/v1/project/' + project.id + '/build/state.svg'" />
                        <pre>[![Build Status]({{ api_host }}/v1/project/{{ project.id }}/build/state.svg)]({{ dashboard_host }}/dashboard/project/{{ project.id }})</pre>
                    </div>
                    <div class="m-t-md">
                        <img :src="api_host + '/v1/project/' +  project.id + '/build/tests.svg'" />
                        <pre>[![Test Status]({{ api_host }}/v1/project/{{ project.id }}/build/tests.svg)]({{ dashboard_host }}/dashboard/project/{{ project.id }})</pre>
                    </div>
                </md-list-item>
            </md-list>
        </md-list-expand>
    </md-list-item>
</template>

<script>
import store from '../../store'

export default {
    props: ['project'],
    created () {
        this.api_host = store.state.settings.INFRABOX_API_URL
        this.dashboard_host = store.state.settings.INFRABOX_DASHBOARD_URL
    }
}
</script>
