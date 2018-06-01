<template>
    <div>
        <md-table-card class="clean-card add-overflow">
            <md-table class="min-medium">
                <md-table-header>
                    <md-table-row>
                        <md-table-head>Filename</md-table-head>
                        <md-table-head>Size</md-table-head>
                    </md-table-row>
                </md-table-header>

                <md-table-body>
                    <md-table-row v-for="a in job.archive" :key="a.filename">
                        <md-table-cell><a @click="job.downloadArchive(a.filename)">{{ a.filename }}</a></md-table-cell>
                        <md-table-cell>{{ Math.round(a.size / 1024) }} kb</md-table-cell>
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
