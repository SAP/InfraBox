<template>
    <span>
        <span v-if="state=='queued'">
            <md-icon md-theme="queued" class="md-primary" style="font-size: 150%">
                <i class="fa fa-fw fa-pause-circle-o"></i>
                <md-tooltip>queued</md-tooltip>
            </md-icon>
        </span>
        <span v-if="state=='scheduled'">
            <md-icon md-theme="scheduled" class="md-primary" style="font-size: 150%">
                <i class="fa fa-fw fa-th-list"></i>
                <md-tooltip>scheduled</md-tooltip>
            </md-icon>
        </span>
        <span v-if="state=='running'">
            <md-icon md-theme="running" class="md-primary" style="font-size: 150%">
                <i class="fa fa-fw fa-dot-circle-o"></i>
                <md-tooltip>running</md-tooltip>
            </md-icon>
        </span>
        <span v-if="state=='finished' || state=='ok'">
            <md-icon md-theme="finished" class="md-primary">
                <i class="fa fa-fw fa-check"></i>
                </md-icon>
            <md-tooltip>finished</md-tooltip>
        </span>
        <span v-if="state=='skipped'">
            <md-icon md-theme="skipped" class="md-size-2x md-primary" style="font-size: 150%">
                <i class="fa fa-fw fa-share"></i>
                <md-tooltip>skipped</md-tooltip>
            </md-icon>
        </span>
        <span v-if="state=='failure'">
            <md-icon md-theme="failure" class="md-primary" style="font-size: 150%">
                <i class="fa fa-fw fa-bolt"></i>
                <md-tooltip>failed</md-tooltip>
            </md-icon>
        </span>
        <span v-if="state=='error'">
            <md-icon md-theme="error" class="md-primary" style="font-size: 150%">
                <i class="fa fa-fw fa-bomb"></i>
                <md-tooltip>error</md-tooltip>
            </md-icon>
        </span>
        <span v-if="state=='killed'">
            <md-icon md-theme="killed" class="md-primary" style="font-size: 150%">
                <i class="fa fa-fw fa-ban"></i>
                <md-tooltip>killed</md-tooltip>
            </md-icon>
        </span>
    </span>
</template>

<script>
export default {
    props: ['state']
}
</script>
