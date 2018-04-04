<template>
    <div>
        <span v-if="date">{{ moment(date) }}</span>
        <span v-if="!date">not started yet</span>
    </div>
</template>

<script>
import moment from 'moment'

export default {
    props: ['date'],
    methods: {
        moment (v) {
            return moment(v).format('lll')
        }
    }
}
</script>
