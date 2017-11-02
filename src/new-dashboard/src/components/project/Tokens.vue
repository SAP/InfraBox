<template>
    <md-list-item class="bg-white">
        <md-icon>bookmark</md-icon>
        <span>Tokens</span>

        <md-list-expand>
            <md-list class="m-t-md m-b-md">
                <md-list-item class="md-inset m-r-xl">
                    <md-input-container class="m-r-xl">
                        <label>Token Description (e.g. &quot;Token for Jira Integration&quot;)</label>
                        <md-input required></md-input>
                    </md-input-container>
                    <md-switch v-model="scopePush" id="scope-push" name="scope-push" md-theme="running" class="md-accent">Push
                    <md-tooltip>Set scope &quot;push&quot;</md-tooltip></md-switch>
                    <md-switch v-model="scopePull" id="scope-pull" name="scope-pull" md-theme="running" class="md-accent">Pull
                    <md-tooltip>Set scope &quot;pull&quot;</md-tooltip></md-switch>
                    <md-button class="md-icon-button md-list-action">
                        <md-icon md-theme="running" class="md-primary">add_circle</md-icon>
                        <md-tooltip>Add new token</md-tooltip>
                    </md-button>
                </md-list-item>
                <md-list-item  v-for="token in project.tokens" :key="token.id" class="md-inset">
                    {{ token.description }}
                    <md-button type="submit" class="md-icon-button md-list-action" @click="$refs.snackbar.open()">
                        <md-icon class="md-primary">delete</md-icon>
                        <md-tooltip>Delete token permanently</md-tooltip>
                    </md-button>
                </md-list-item>
            </md-list>
        </md-list-expand>
        <md-snackbar :md-position="vertical + ' ' + horizontal" ref="snackbar" :md-duration="duration">
            <span><i class="fa fa-trash"></i><span class="m-l-xl"> Token successfully deleted.</span></span>
        </md-snackbar>
    </md-list-item>
</template>

<script>
export default {
    props: ['project'],
    data: () => ({
        scopePush: '',
        scopePull: '',
        vertical: 'top',
        horizontal: 'center',
        duration: 4000
    }),
    created () {
        this.project._loadTokens()
    },
    methods: {
        open () {
            this.$refs.snackbar.open()
        }
    }
}
</script>
