<template>
<div class="m-sm full-height">
    <md-card md-theme="white" class="full-height clean-card">
        <md-card-header>
            <md-card-header-text class="setting-list">
                <md-icon>bookmark</md-icon>
                <span>Tokens</span>
            </md-card-header-text>
        </md-card-header>
        <md-card-area>
            <md-list class="m-t-md m-b-md">
                <md-list-item>
                    <md-input-container class="m-r-xl">
                        <label>Token Description (e.g. &quot;Jenkins Integration&quot;)</label>
                        <md-input required v-model="description" @keyup.enter.native="addToken"></md-input>
                    </md-input-container>
                    <md-button :disabled="disableAdd" class="md-icon-button md-list-action" @click="addToken">
                        <md-icon md-theme="running" class="md-primary">add_circle</md-icon>
                        <md-tooltip>Add new token</md-tooltip>
                    </md-button>
                </md-list-item>
                <md-list-item  v-for="token in project.tokens" :key="token.id">
                    <div class="md-input-container m-r-xl md-theme-white">
                        {{ token.description }}
                    </div>
                    <md-button type="submit" class="md-icon-button md-list-action" @click="project.deleteToken(token.id)">
                        <md-icon class="md-primary">delete</md-icon>
                        <md-tooltip>Delete token permanently</md-tooltip>
                    </md-button>
                </md-list-item>
            </md-list>
        </md-card-area>
    </md-card>
    <md-dialog ref="dialog">
        <md-dialog-title>Authentication Token</md-dialog-title>

        <md-dialog-content>
            Please save your token at a secure place. We will not show it to you again.<br><br>

            <pre class="token-pre">{{ token }}</pre><br><br>

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
        token: '',
        disableAdd: true
    }),
    created () {
        this.project._loadTokens()
    },
    watch: {
        description () {
            this.disableAdd = !this.description || this.description.length < 3
        }
    },
    methods: {
        addToken () {
            this.project.addToken(this.description)
                .then((token) => {
                    this.token = token
                    this.$refs['dialog'].open()
                })
            this.description = ''
        }
    }
}
</script>

<style scoped>
.token-pre {
    white-space: pre-wrap;       /* Since CSS 2.1 */
    white-space: -moz-pre-wrap;  /* Mozilla, since 1999 */
    white-space: -pre-wrap;      /* Opera 4-6 */
    white-space: -o-pre-wrap;    /* Opera 7 */
    word-wrap: break-word;       /* Internet Explorer 5.5+ */
}
</style>
