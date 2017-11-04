<template>
    <div>
        <md-table-card class="console-table">
            <md-table>
                <md-table-header class="text-right">
                    <md-table-row>
                        <md-table-head class="console-table"><span class="p-xxl">Console Output</span></md-table-head>
                        <md-table-head class="console-table text-right"><span class="text-right">Lines</span></md-table-head>
                        <md-table-head class="console-table text-right"><span class="text-right">Duration</span></md-table-head>
                    </md-table-row>
                </md-table-header>
                <md-table-body>
                    <md-table-row v-for="section of job.sections" :key="section.text">
                        <md-table-cell class="console-table"><md-card-expand>
                            <md-card-actions class="console-table text-left text-top">
                                <md-button class="md-icon-button md-raised md-accent m-r-md" md-expand-trigger>
                                    <md-icon>expand_less</md-icon>
                                </md-button>
                                <span class="m-l-md md-body-2" style="flex: 1">
                                    {{ section.text }}
                                </span>
                                </md-card-actions>
                                <md-card-content class="no-padding">
                                    <pre class="inherit-font no-margin p-l-xxl" v-html="section.lines_html"></pre>
                                </md-card-content>
                            </md-card-expand>
                        </md-table-cell>
                        <md-table-cell class="console-table text-top">
                            <div class="p-t-sm">{{ section.linesInSection }} lines</div>
                        </md-table-cell>
                        <md-table-cell class="console-table text-top">
                            <div class="p-t-sm">{{ section.duration }} seconds</div>
                        </md-table-cell>
                    </md-table-row>
                </md-table-body>
            </md-table>
        </md-table-card>
    </div>
</template>

<script>
export default {
    name: 'Console',
    props: ['job']
}
</script>

<style scoped>
    .console-table {
        background-color: #273439 !important;
        color: white !important;
        box-shadow: none;
    }
</style>
