<template>
    <md-table-card>
        <md-toolbar class="md-dense">
            <h3 class="md-title">
                Collaborators
            </h3>
            <md-button md-theme="running" class="md-icon-button md-raised md-primary">
                  <md-icon>add</md-icon>
            </md-button>
        </md-toolbar>

        <md-card-content>
            <md-table>
                <md-table-header>
                    <md-table-row>
                        <md-table-head>Avatar</md-table-head>
                        <md-table-head>Username</md-table-head>
                        <md-table-head>Email</md-table-head>
                        <md-table-head>Remove</md-table-head>
                    </md-table-row>
                </md-table-header>

                <md-table-body>
                    <md-table-row v-for="co in project.collaborators" :key="co.id">
                        <md-table-cell>
                            <span>
                                <img v-if="co.avatar_url" alt="image" class="img-circle" style="width: 40px;" :src="co.avatar_url"/>
                                <img v-if="!co.avatar_url" alt="image" class="img-circle" style="width: 40px;" src="../../../static/logo_image_only.png"/>
                            </span>
                        </md-table-cell>
                        <md-table-cell>{{ co.username }}</md-table-cell>
                        <md-table-cell>{{ co.email }}</md-table-cell>
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
        this.project._loadCollaborators()
    }
}
</script>
