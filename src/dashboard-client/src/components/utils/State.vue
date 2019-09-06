<template>
    <span>
        <span v-if="state=='queued'">
            <div class="bg-light circle-icon">
                <i class="fa fa-fw fa-pause-circle-o"></i>
                <md-tooltip>{{ state }}</md-tooltip>
            </div>
        </span>
        <span v-if="state=='scheduled'">
            <div class="bg-light circle-icon">
                <i class="fa fa-fw fa-th-list"></i>
                <md-tooltip>{{ state }}</md-tooltip>
            </div>
        </span>
        <span v-if="state=='running'">
            <div class="bg-running circle-icon">
                <i class="fa fa-fw fa-dot-circle-o"></i>
                <md-tooltip>{{ state }}</md-tooltip>
            </div>
        </span>
        <span v-if="state=='finished' || state=='ok'">
            <div class="bg-success circle-icon">
                <i class="fa fa-fw fa-check"></i>
            </div>
            <md-tooltip>{{ state }}</md-tooltip>
        </span>
        <span v-if="state=='skipped'">
            <div class="bg-light circle-icon">
                <i class="fa fa-fw fa-share"></i>
                <md-tooltip>{{ state }}</md-tooltip>
            </div>
        </span>
        <span v-if="state=='failure'">
            <div class="bg-failure circle-icon">
                <i class="fa fa-fw fa-bolt"></i>
                <md-tooltip>{{ state }}</md-tooltip>
            </div>
        </span>
        <span v-if="state=='unstable'">
            <div class="bg-unstable circle-icon">
                <i class="fa fa-fw fa-bolt"></i>
                <md-tooltip>{{ state }}</md-tooltip>
            </div>
        </span>
        <span v-if="state=='error'">
            <div class="bg-error circle-icon">
                <i class="fa fa-fw fa-exclamation"></i>
                <md-tooltip>{{ state }}</md-tooltip>
            </div>
        </span>
        <span v-if="state=='killed'">
            <div class="bg-light circle-icon">
                <i class="fa fa-fw fa-ban"></i>
                <md-tooltip>{{ state }}</md-tooltip>
            </div>
        </span>
    </span>
</template>

<script>
export default {
    props: ['state']
}
</script>
