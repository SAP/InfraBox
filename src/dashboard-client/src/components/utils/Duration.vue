<template>
    <div>
        <span v-if="start && end">{{ duration(end - start) }}</span>
        <md-tooltip v-if="end && start">{{ duration_minutes(end - start) }}</md-tooltip>
        <span v-if="start && !end">still running</span>
        <span v-if="!start">not started yet</span>
    </div>
</template>

<script>
import moment from 'moment'

export default {
    props: ['start', 'end'],
    methods: {
        duration (v) {
            return moment.duration(v, 'ms').humanize()
        },
        duration_minutes (v) {
            let d = moment.duration(v, 'ms')
            return Math.floor(d.asHours()) + moment.utc(d.asMilliseconds()).format(':mm:ss')
        }
    }
}
</script>
