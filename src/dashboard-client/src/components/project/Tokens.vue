<template>
<div>
    <md-list md-theme="white">
        <md-list-item class="setting-list">
            <md-icon>bookmark</md-icon>
            <span>Tokens</span>

            <md-list-expand>
                <md-list class="m-t-md m-b-md">
                    <md-list-item class="md-inset m-r-xl">
                        <md-input-container class="m-r-xl">
                            <label>Token Description (e.g. &quot;Token for Jenkins Integration&quot;)</label>
                            <md-input required v-model="description"></md-input>
                        </md-input-container>
                        <md-button class="md-icon-button md-list-action" @click="addToken">
                            <md-icon md-theme="running" class="md-primary">add_circle</md-icon>
                            <md-tooltip>Add new token</md-tooltip>
                        </md-button>
                    </md-list-item>
                    <md-list-item  v-for="token in project.tokens" :key="token.id" class="md-inset">
                        {{ token.description }}
                        <md-button type="submit" class="md-icon-button md-list-action" @click="project.deleteToken(token.id)">
                            <md-icon class="md-primary">delete</md-icon>
                            <md-tooltip>Delete token permanently</md-tooltip>
                        </md-button>
                    </md-list-item>
                </md-list>
            </md-list-expand>
        </md-list-item>
    </md-list>
    <md-dialog ref="dialog">
        <md-dialog-title>Authentication Token</md-dialog-title>

        <md-dialog-content>
            Please save your token at a secure place. We will not show it to you again.<br><br>

            <pre>{{ token }}</pre><br><br>

            You may later us it with infraboxcli:<br>
            <pre>$ export INFRABOX_CLI_TOKEN=&lt;YOUR_TOKEN_VALUE&gt;
$ infrabox {push|pull|...}
            </pre>
        </md-dialog-content>

        <md-dialog-actions>
            <md-button class="md-primary" @click="$refs['dialog'].close()">OK</md-button>
        </md-dialog-actions>
    </md-dialog>
</div>
</template>

<script>
export default {
    props: ['project'],
    data: () => ({
        description: '',
        token: ''
    }),
    created () {
        this.project._loadTokens()
    },
    methods: {
        addToken () {
            this.project.addToken(this.description)
            .then((token) => {
                this.token = token
                this.$refs['dialog'].open()
            })
        }
    }
}
</script>
