<template>
    <div>
        <md-table-card class="clean-card add-overflow">
            <md-table class="min-medium">
                <md-table-header>
                    <md-table-row>
                        <md-table-head>Filename</md-table-head>
                        <md-table-head>Size</md-table-head>
                        <md-table-head>Download</md-table-head>
                    </md-table-row>
                </md-table-header>

                <md-table-body>
                    <md-table-row v-for="a in job.archive" :key="a.filename">
                        <md-table-cell>{{ a.filename }}</md-table-cell>
                        <md-table-cell>{{ a.size }} ms</md-table-cell>
                        <md-table-cell>
                            <md-button class="md-icon-button md-primary"
                                       @click="job.downloadArchive(a.filename)">
                                <md-icon>close</md-icon>
                            </md-button>
                        </md-table-cell>
                    </md-table-row>
                </md-table-body>
            </md-table>
        </md-table-card>
    </div>
</template>

<script>
export default {
    name: 'Archive',
    props: ['job']
}
</script>
