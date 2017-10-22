<template>
    <md-table-card>
        <md-toolbar class="md-dense">
            <h3 class="md-title">
                Secrets
            </h3>
            <md-button class="md-icon-button md-raised">
                  <md-icon>add</md-icon>
            </md-button>
        </md-toolbar>

        <md-card-content>
            <md-table>
                <md-table-header>
                    <md-table-row>
                        <md-table-head>Secret Name</md-table-head>
                        <md-table-head>Delete</md-table-head>
                    </md-table-row>
                </md-table-header>

                <md-table-body>
                    <md-table-row v-for="secret in project.secrets" :key="secret.id">
                        <md-table-cell>{{ secret.name }}</md-table-cell>
                        <md-table-cell>
                            <md-button class="md-icon-button md-raised">
                                  <md-icon>delete</md-icon>
                            </md-button>
                        </md-table-cell>
                    </md-table-row>
                </md-table-body>
            </md-table>
        </md-card-content>
    </md-table-card>
</template>

<script>
export default {
    props: ['project'],
    created () {
        this.project._loadSecrets()
    }
}
</script>
