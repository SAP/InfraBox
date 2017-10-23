<template>
    <span>
        <span v-if="state=='queued'">
            <md-icon md-theme="queued" class="md-primary" style="font-size: 150%">
                <i class="fa fa-pause-circle-o"></i>
            </md-icon>
        </span>
        <span v-if="state=='scheduled'">
            <md-icon md-theme="scheduled" class="md-primary" style="font-size: 150%">
                <i class="fa fa-th-list"></i>
            </md-icon>
        </span>
        <span v-if="state=='running'">
            <md-icon md-theme="running" class="md-primary" style="font-size: 150%">
                <i class="fa fa-dot-circle-o"></i>
            </md-icon>
        </span>
        <span v-if="state=='finished'">
            <md-icon md-theme="finished" class="md-primary">
                <i class="fa fa-check"></i>
            </md-icon>
        </span>
        <span v-if="state=='skipped'">
            <md-icon md-theme="skipped" class="md-size-2x md-primary" style="font-size: 150%">
                <i class="fa fa-share"></i>
            </md-icon>
        </span>
        <span v-if="state=='failure'">
            <md-icon md-theme="failure" class="md-primary" style="font-size: 150%">
                <i class="fa fa-bolt"></i>
            </md-icon>
        </span>
        <span v-if="state=='error'">
            <md-icon md-theme="error" class="md-primary" style="font-size: 150%">
                <i class="fa fa-bomb"></i>
            </md-icon>
        </span>
        <span v-if="state=='killed'">
            <md-icon md-theme="killed" class="md-primary" style="font-size: 150%">
                <i class="fa fa-ban"></i>
            </md-icon>
        </span>
    </span>
</template>

<script>
export default {
    props: ['state']
}
</script>
