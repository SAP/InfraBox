<template>
    <div>
        <md-table-card class="clean-card add-overflow">
            <md-table class="min-medium">
                <md-table-header>
                    <md-table-row>
                        <md-table-head>Test</md-table-head>
                        <md-table-head>Suite</md-table-head>
                        <md-table-head>Duration</md-table-head>
                        <md-table-head>Result</md-table-head>
                        <md-table-head>Details</md-table-head>
                    </md-table-row>
                </md-table-header>

                <md-table-body>
                    <md-table-row v-for="t in job.tests" :id="t.name+t.suite" :key="t.name+t.suite">
                        <md-table-cell>{{ t.name }}</md-table-cell>
                        <md-table-cell>{{ t.suite }}</md-table-cell>
                        <md-table-cell>{{ t.duration }} ms</md-table-cell>
                        <md-table-cell><ib-state :state="t.state"></ib-state></md-table-cell>
                        <md-table-cell>
                        </md-table-cell>
                    </md-table-row>
                </md-table-body>
            </md-table>
        </md-table-card>
    </div>
</template>

<script>
export default {
    name: 'TestList',
    props: ['job'],
    created () {
        this.job.loadTests()
    }
}
</script>
