<template>
    <span>
        <span v-if="state=='queued'">
            <md-icon md-theme="queued" class="md-primary" md-iconset="fa fa-pause-circle-o" style="font-size: 150%"></md-icon>
        </span>
        <span v-if="state=='scheduled'">
            <md-icon md-theme="scheduled" class="md-primary" md-iconset="fa fa-th-list" style="font-size: 150%"></md-icon>
        </span>
        <span v-if="state=='running'">
            <md-icon md-theme="running" class="md-primary" md-iconset="fa fa-dot-circle-o" style="font-size: 150%"></md-icon>
        </span>
        <span v-if="state=='finished'">
            <md-icon md-theme="finished" class="md-primary" md-iconset="fa fa-check" style="font-size: 150%"></md-icon>
        </span>
        <span v-if="state=='skipped'">
            <md-icon md-theme="skipped" class="md-size-2x md-primary" md-iconset="fa fa-share" style="font-size: 150%"></md-icon>
        </span>
        <span v-if="state=='failure'">
            <md-icon md-theme="failure" class="md-primary" md-iconset="fa fa-bolt" style="font-size: 150%"></md-icon>
        </span>
        <span v-if="state=='error'">
            <md-icon md-theme="error" class="md-primary" md-iconset="fa fa-bomb" style="font-size: 150%"></md-icon>
        </span>
        <span v-if="state=='killed'">
            <md-icon md-theme="killed" class="md-primary" md-iconset="fa fa-ban" style="font-size: 150%"></md-icon>
        </span>
    </span>
</template>

<script>
export default {
    props: ['state']
}
</script>
