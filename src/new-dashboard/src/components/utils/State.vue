<template>
    <div>
        <span v-if="state=='queued'"><i class="fa fa-pause-circle-o icon-paused-negative btn-circle-small"></i></span>
        <span v-if="state=='scheduled'"><i class="fa fa-th-list icon-scheduled-negative btn-circle-small"></i></span>
        <span v-if="state=='running'"><i class="fa fa-dot-circle-o icon-running-negative btn-circle-small"></i></span>
        <span v-if="state=='finished'"><i class="fa fa-check icon-success-negative btn-circle-small"></i></span>
        <span v-if="state=='skipped'"><i class="fa fa-share icon-skipped-negative btn-circle-small"></i></span>
        <span v-if="state=='failure'"><i class="fa fa-bolt icon-failure-negative btn-circle-small"></i></span>
        <span v-if="state=='error'"><i class="fa fa-bomb icon-error-negative btn-circle-small"></i></span>
        <span v-if="state=='killed'"><i class="fa fa-ban icon-white-negative btn-circle-small"></i></span>
    </div>
</template>

<script>
export default {
    props: ['state']
}
</script>
