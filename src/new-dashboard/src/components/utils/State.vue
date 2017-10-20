<template>
    <div>
        <span v-if="state=='queued'">
            <md-icon md-theme="queued" class="md-primary" md-iconset="fa fa-pause-circle-o"></md-icon>
        </span>
        <span v-if="state=='scheduled'">
            <md-icon md-theme="scheduled" class="md-primary" md-iconset="fa fa-th-list"></md-icon>
        </span>
        <span v-if="state=='running'">
            <md-icon md-theme="running" class="md-primary" md-iconset="fa fa-dot-circle-o"></md-icon>
        </span>
        <span v-if="state=='finished'">
            <md-icon md-theme="finished" class="md-primary" md-iconset="fa fa-check"></md-icon>
        </span>
        <span v-if="state=='skipped'">
            <md-icon md-theme="skipped" class="md-primary" md-iconset="fa fa-share"></md-icon>
        </span>
        <span v-if="state=='failure'">
            <md-icon md-theme="failure" class="md-primary" md-iconset="fa fa-bolt"></md-icon>
        </span>
        <span v-if="state=='error'">
            <md-icon md-theme="error" class="md-primary" md-iconset="fa fa-bomb"></md-icon>
        </span>
        <span v-if="state=='killed'">
            <md-icon md-theme="killed" class="md-primary" md-iconset="fa fa-ban"></md-icon>
        </span>
    </div>
</template>

<script>
export default {
    props: ['state']
}
</script>
