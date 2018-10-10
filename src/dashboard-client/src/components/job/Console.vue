<template>
    <div>
        <md-table-card class="console-table">
            <md-layout  md-column  md-align="center" width="100%" v-if="job.message">
                <md-card :md-theme="job.state" class="md-primary p-t-xs p-b-xs p-l-md p-r-md font-roboto">
                    <span><i class="fa fa-exclamation-triangle p-r-sm"></i> {{ job.message }}</span>
                </md-card>
            </md-layout>
            <md-table>
                <md-table-header class="text-right">
                    <md-table-row>
                        <md-table-head class="console-table"><span class="p-xxl">Console Output</span></md-table-head>
                        <md-table-head class="console-table" style="text-align: right"></md-table-head>
                        <md-table-head class="console-table" style="text-align: right">Lines</md-table-head>
                        <md-table-head class="console-table" style="text-align: right">Duration</md-table-head>
                    </md-table-row>
                </md-table-header>
                <md-table-body>
                    <md-table-row v-for="section of job.sections" :key="section.id" >
                        <md-table-cell class="console-table">
                            <md-card-expand>
                                <md-card-actions class="console-table text-left text-top">
                                <md-button
                                    md-theme="skipped"
                                    class="md-icon-button md-primary md-raised md-dense"
                                    v-bind:style="{ background: section.color}"
                                    md-expand-trigger>
                                    <md-icon>expand_less</md-icon>
                                </md-button>
                                <span class="m-l-md md-body-2" style="flex: 1">
                                    {{ section.text }}
                                </span>
                                </md-card-actions>
                                <md-card-content class="no-padding">
                                    <pre class="inherit-font no-margin p-l-xxl wrap-text" v-html="section.lines_html"></pre>
                                </md-card-content>
                            </md-card-expand>
                        </md-table-cell>
                        <md-table-cell class="console-table text-top text-right dont-wrap">
                            <div v-if="section.labels['error']" class="bg-failure circle-icon">
                                <i class="fa fa-fw fa-exclamation-circle"></i>
                                <md-tooltip>{{ section.labels.error }} Errors</md-tooltip>
                            </div>
                            <div v-if="section.labels['warning']" class="bg-warning circle-icon">
                                <i class="fa fa-fw fa-exclamation-circle"></i>
                                <md-tooltip>{{ section.labels.warning }} Warnings</md-tooltip>
                            </div>
                        </md-table-cell>
                        <md-table-cell class="console-table text-top text-right dont-wrap">
                            <div class="p-t-sm">{{ section.linesInSection }} Lines</div>
                        </md-table-cell>
                        <md-table-cell class="console-table text-top text-right dont-wrap">
                            <div class="p-t-sm">{{ section.duration }} Seconds</div>
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
    props: ['job'],
    created: function () {
        this.job.loadConsole()
    }
}
</script>

<style scoped>
    .console-table {
        background-color: #273439 !important;
        color: white !important;
        font-family: monospace;
        box-shadow: none;
    }

    .font-roboto {
        font-family: Roboto;
        font-weight: 500;
    }
</style>
