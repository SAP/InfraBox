<template>
    <md-list-item class="setting-list">
        <md-icon>people</md-icon>
        <span>Collaborators</span>

        <md-list-expand>
            <md-list class="m-t-md m-b-md md-double-line">
                <md-list-item class="md-inset m-r-xl">
                    <md-avatar class="md-avatar-icon">
                        <md-icon>face</md-icon>
                    </md-avatar>

                    <div class="md-list-text-container">
                        <span>
                            <md-input-container>
                                <label>User Name</label>
                                <md-input required></md-input>
                            </md-input-container>
                        </span>
                    </div>

                    <md-button class="md-icon-button md-list-action">
                        <md-icon md-theme="running" class="md-primary">add_circle</md-icon>
                        <md-tooltip>Add collaborator</md-tooltip>
                    </md-button>
                </md-list-item>
                <md-list-item v-for="co in project.collaborators" :key="co.id" class="md-inset m-r-xl">
                    <md-avatar>
                        <img v-if="co.avatar_url" alt="image" class="img-circle" style="width: 40px;" :src="co.avatar_url"/>
                        <img v-if="!co.avatar_url" alt="image" class="img-circle" style="width: 40px;" src="../../../static/logo_image_only.png"/>
                    </md-avatar>

                    <div class="md-list-text-container">
                        <span>{{ co.username }}</span>
                        <span>{{ co.email }}</span>
                    </div>

                    <md-button type="submit" class="md-icon-button md-list-action" @click="$refs.snackbar.open()">
                        <md-icon class="md-primary">delete</md-icon>
                        <md-tooltip>Remove collaborator</md-tooltip>
                    </md-button>
                </md-list-item>
            </md-list>
        </md-list-expand>
        <md-snackbar :md-position="vertical + ' ' + horizontal" ref="snackbar" :md-duration="duration">
            <span>
                  <i class="fa fa-chain-broken"></i>
                <span class="m-l-xl"> Collaborator successfully removed.</span>
            </span>
        </md-snackbar>
    </md-list-item>
</template>

<script>
export default {
    props: ['project'],
    data: () => ({
        vertical: 'top',
        horizontal: 'center',
        duration: 4000
    }),
    created () {
        this.project._loadCollaborators()
    },
    methods: {
        open () {
            this.$refs.snackbar.open()
        }
    }
}
</script>
