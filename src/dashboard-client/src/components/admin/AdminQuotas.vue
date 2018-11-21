<template>
    <md-card class="main-card">
        <div>
            <div v-if="this.Quotatype == null">
                <div>
                    <quotas-list-users Quotatype="user"></quotas-list-users>
                </div>
                <div>
                    <quotas-list-users Quotatype="project"></quotas-list-users>
                </div>
            </div>

            <div v-if="this.Quotatype == 'user'">
                <div>
                    <quotas-list-users Quotatype="user" v-bind:objectID="this.objectID"></quotas-list-users>
                </div>
            </div>

            <div v-if="this.Quotatype == 'project'">
                <div>
                    <quotas-list-users Quotatype="project" v-bind:objectID="this.objectID"></quotas-list-users>
                </div>
            </div>
        </div>
    </md-card>
</template>



<script>

import QuotasList from './QuotasList'

export default {
    props: ['admin', 'Quotatype', 'objectID'],
    components: {
        'quotas-list-users': QuotasList
    }

}
</script>

<style scoped>
.fix-padding {
    padding-top: 7px !important;
    padding-bottom: 22px !important;
    padding-left: 0 !important;
}

</style>