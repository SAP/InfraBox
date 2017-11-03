<template>
    <md-list-item class="setting-list">
        <md-icon>security</md-icon>
        <span>Secrets</span>

        <md-list-expand>
            <md-list class="m-t-md m-b-md">
                <md-list-item class="md-inset m-r-xl">
                    <md-input-container class="m-r-sm">
                        <label>Secret Name</label>
                        <md-input required></md-input>
                    </md-input-container>
                    <md-input-container class="m-l-sm">
                        <label>Secret Value</label>
                        <md-input required></md-input>
                    </md-input-container>
                    <md-button class="md-icon-button md-list-action">
                        <md-icon md-theme="running" class="md-primary">add_circle</md-icon>
                        <md-tooltip>Add new secret</md-tooltip>
                    </md-button>
                </md-list-item>
                <md-list-item v-for="secret in project.secrets" :key="secret.id" class="md-inset">
                    {{ secret.name }}
                    <md-button type="submit" class="md-icon-button md-list-action" @click="$refs.snackbar.open()">
                        <md-icon class="md-primary">delete</md-icon>
                        <md-tooltip>Delete secret permanently</md-tooltip>
                    </md-button>
                </md-list-item>
            </md-list>
        </md-list-expand>
        <md-snackbar :md-position="vertical + ' ' + horizontal" ref="snackbar" :md-duration="duration">
            <span><i class="fa fa-trash"></i><span class="m-l-xl"> Secret successfully deleted.</span></span>
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
        this.project._loadSecrets()
    },
    methods: {
        open () {
            this.$refs.snackbar.open()
        }
    }
}
</script>
