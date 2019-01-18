<template>
    <div>
        <md-table-card class="clean-card add-overflow">
            <md-table class="min-medium" @sort="sort">
                <md-table-header>
                    <md-table-row>
                        <md-table-head md-sort-by="filename">Filename</md-table-head>
                        <md-table-head md-sort-by="size">Size</md-table-head>
                        <md-table-head >View</md-table-head>
                    </md-table-row>
                </md-table-header>

                <md-table-body>
                    <md-table-row v-for="a in files" :key="a.filename">
                        <md-table-cell><a @click="job.downloadArchive(a.filename)">{{ a.filename }}</a></md-table-cell>
                        <md-table-cell>{{ Math.round(a.size / 1024) }} kb</md-table-cell>
                        <md-table-cell><a @click="job.downloadArchive(a.filename, 'true')">View Online</a></md-table-cell>
                    </md-table-row>
                </md-table-body>
            </md-table>
        </md-table-card>
    </div>
</template>

<script>
import _ from 'underscore'

export default {
    name: 'Archive',
    props: ['job'],
    data: function () {
        return {
            field: null,
            order: 'asc'
        }
    },
    computed: {
        files: function () {
            let a = _.sortBy(this.job.archive, (j) => {
                return j[this.field]
            })

            if (this.order === 'desc') {
                a = a.reverse()
            }

            return a
        }
    },
    methods: {
        sort (opt) {
            this.field = opt.name
            this.order = opt.type
        }
    }
}
</script>
