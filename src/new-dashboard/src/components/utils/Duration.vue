<template>
    <div>
        <span v-if="end && start">{{ duration(end - start) }}</span>
        <span v-if="!end">still running</span>
    </div>
</template>

<script>
import moment from 'moment'

export default {
    props: ['start', 'end'],
    methods: {
        duration (v) {
            return moment.duration(v, 'ms').humanize()
        }
    }
}
</script>
