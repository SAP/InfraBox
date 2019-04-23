<template>
    <span>
        <span v-if="state=='queued'">
            <md-avatar md-theme="queued" class="md-avatar-icon md-large md-primary">
                <md-icon>
                    <i class="fa fa-fw fa-pause-circle-o"></i>
                </md-icon>
            </md-avatar>
            <md-tooltip>{{ state }}</md-tooltip>
        </span>
        <span v-if="state=='scheduled'">
            <md-avatar md-theme="scheduled" class="md-avatar-icon md-large md-primary">
                <md-icon>
                    <i class="fa fa-fw fa-th-list"></i>
                </md-icon>
            </md-avatar>
            <md-tooltip>{{ state }}</md-tooltip>
        </span>
        <span v-if="state=='running'">
            <md-avatar md-theme="running" class="md-avatar-icon md-large md-primary">
                <md-icon>
                    <i class="fa fa-fw fa-dot-circle-o"></i>
                </md-icon>
            </md-avatar>
            <md-tooltip>{{ state }}</md-tooltip>
        </span>
        <span v-if="state=='finished' || state=='ok'">
            <md-avatar md-theme="finished" class="md-avatar-icon md-large md-primary">
                <md-icon>
                    <i class="fa fa-fw fa-check"></i>
                </md-icon>
            </md-avatar>
            <md-tooltip>{{ state }}</md-tooltip>
        </span>
        <span v-if="state=='skipped'">
            <md-avatar md-theme="skipped" class="md-avatar-icon md-large md-primary">
                <md-icon>
                    <i class="fa fa-fw fa-share"></i>
                </md-icon>
            </md-avatar>
            <md-tooltip>{{ state }}</md-tooltip>
        </span>
        <span v-if="state=='failure'">
            <md-avatar md-theme="failure" class="md-avatar-icon md-large md-primary">
                <md-icon>
                    <i class="fa fa-fw fa-bolt"></i>
                </md-icon>
            </md-avatar>
            <md-tooltip>{{ state }}</md-tooltip>
        </span>
        <span v-if="state=='unstable'">
            <md-avatar md-theme="unstable" class="md-avatar-icon md-large md-primary">
                <md-icon>
                    <i class="fa fa-fw fa-bolt"></i>
                </md-icon>
            </md-avatar>
            <md-tooltip>{{ state }}</md-tooltip>
        </span>
        <span v-if="state=='error'">
            <md-avatar md-theme="error" class="md-avatar-icon md-large md-primary">
                <md-icon>
                    <i class="fa fa-fw fa-bomb"></i>
                </md-icon>
            </md-avatar>
            <md-tooltip>{{ state }}</md-tooltip>
        </span>
        <span v-if="state=='killed'">
            <md-avatar md-theme="killed" class="md-avatar-icon md-large md-primary">
                <md-icon>
                    <i class="fa fa-fw fa-ban"></i>
                </md-icon>
            </md-avatar>
            <md-tooltip>{{ state }}</md-tooltip>
        </span>
    </span>
</template>

<script>
export default {
    props: ['state']
}
</script>
