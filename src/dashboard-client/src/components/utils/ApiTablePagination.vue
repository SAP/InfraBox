<template>
    <div class="md-table-pagination">
        <template v-if="mdPageOptions !== false">
            <span class="md-table-pagination-label">{{ mdLabel }}</span>
            <md-select v-model="currentPageSize" md-dense md-class="md-pagination-select" @change="$emit('update:mdPageSize', currentPageSize)">
                <md-option v-for="amount in mdPageOptions" :key="amount" :value="amount">{{ amount }}</md-option>
            </md-select>
        </template>

        <span>Page {{ currentPage }} {{ mdSeparator }} {{ totalPages }}</span>

        <md-button class="md-icon-button md-table-pagination-previous" @click="goToPrevious()" :disabled="!('prev' in navData)">
            <md-icon>keyboard_arrow_left</md-icon>
        </md-button>

        <md-button class="md-icon-button md-table-pagination-next" @click="goToNext()" :disabled="!('next' in navData)">
            <md-icon>keyboard_arrow_right</md-icon>
        </md-button>
    </div>
</template>

<script>
export default {
    name: 'ApiTablePagination',
    props: {
        mdPageSize: {
            type: [String, Number],
            default: 10
        },
        mdPageOptions: {
            type: Array,
            default: () => [10, 25, 50, 100]
        },
        mdPage: {
            type: Number,
            default: 1
        },
        mdLabel: {
            type: String,
            default: 'Rows per page'
        },
        mdSeparator: {
            type: String,
            default: 'of'
        },
        navData: {
            type: Object,
            default: () => { return {} }
        },
        page: {
            type: Number,
            default: 0
        }
    },
    data: () => ({
        currentPageSize: 0,
        currentPage: 0,
        totalPages: 0
    }),
    watch: {
        mdPageSize: {
            immediate: true,
            handler (pageSize) {
                this.currentPageSize = pageSize
            }
        },
        page: {
            immediate: true,
            handler (pageNumber) {
                this.currentPage = pageNumber
                if ('last' in this.navData) {
                    this.totalPages = this.navData.last
                }
            }
        }
    },
    methods: {
        goToPrevious () {
            this.$emit('pagination', this.navData.prev)
        },
        goToNext () {
            this.$emit('pagination', this.navData.next)
        }
    },
    created () {
        this.currentPageSize = this.mdPageSize
    }
}
</script>