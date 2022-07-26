<template>
    <md-layout md-row>
        <md-layout md-column md-gutter md-flex-xsmall="100" md-flex-small="50" md-flex-medium="50" md-flex-large="50" md-flex-xlarge="50" class="b-r thin-border">
            <ib-project-secrets :project="project"></ib-project-secrets>
        </md-layout>
        <md-layout md-column md-gutter md-flex-xsmall="100" md-flex-small="50" md-flex-medium="50" md-flex-large="50" md-flex-xlarge="50" class="b-r thin-border">
            <ib-project-collaborators :project="project"></ib-project-collaborators>
        </md-layout>
        <md-layout md-column md-gutter md-flex-xsmall="100" md-flex-small="50" md-flex-medium="50" md-flex-large="50" md-flex-xlarge="50">
            <ib-project-tokens :project="project"></ib-project-tokens>
        </md-layout>
        <md-layout md-column md-gutter md-flex-xsmall="100" md-flex-small="50" md-flex-medium="50" md-flex-large="50" md-flex-xlarge="50">
            <ib-project-sshkeys :project="project"></ib-project-sshkeys>
        </md-layout>
        <md-layout v-if="project.userHasOwnerRights()" md-column md-gutter md-flex-xsmall="100" md-flex-small="50" md-flex-medium="50" md-flex-large="50" md-flex-xlarge="50">
            <ib-project-visibility :project="project"></ib-project-visibility>
        </md-layout>
        <md-layout md-column md-gutter md-flex-xsmall="100" md-flex-small="100" md-flex-medium="100" md-flex-large="100" md-flex-xlarge="100">
            <ib-Vault :project="project"></ib-Vault>
        </md-layout>
        <md-layout md-column md-gutter md-flex-xsmall="100" md-flex-small="100" md-flex-medium="100" md-flex-large="100" md-flex-xlarge="100">
            <ib-project-cronjobs :project="project"></ib-project-cronjobs>
        </md-layout>
        <md-layout md-column md-gutter md-flex-xsmall="100" md-flex-small="100" md-flex-medium="100" md-flex-large="100" md-flex-xlarge="100">
            <ib-project-pattern :project="project"></ib-project-pattern>
        </md-layout>
        <md-layout md-column md-gutter md-flex-xsmall="100" md-flex-small="100" md-flex-medium="100" md-flex-large="100" md-flex-xlarge="100">
            <ib-project-badges :project="project"></ib-project-badges>
        </md-layout>
    </md-layout>
</template>

<script>
import ProjectSecrets from './Secrets'
import ProjectTokens from './Tokens'
import ProjectCollaborators from './Collaborators'
import ProjectBadges from './Badges'
import ProjectCronJobs from './Cron'
import ProjectSSHKeys from './SSHKeys'
import ProjectVisibility from './Visibility'
import ProjectVault from './Vault'
import ProjectPattern from './Pattern'

export default {
    props: ['project'],
    components: {
        'ib-project-secrets': ProjectSecrets,
        'ib-project-tokens': ProjectTokens,
        'ib-project-collaborators': ProjectCollaborators,
        'ib-project-badges': ProjectBadges,
        'ib-project-cronjobs': ProjectCronJobs,
        'ib-project-visibility': ProjectVisibility,
        'ib-Vault': ProjectVault,
        'ib-project-pattern': ProjectPattern,
        'ib-project-sshkeys': ProjectSSHKeys
    }
}
</script>

<style scoped>

</style>
