<template>
    <md-layout md-row>
        <md-layout md-column md-gutter md-flex-xsmall="100" md-flex-small="50" md-flex-medium="50" md-flex-large="33" md-flex-xlarge="33" class="b-r thin-border">
            <ib-project-secrets :project="project"></ib-project-secrets>
        </md-layout>
        <md-layout md-column md-gutter md-flex-xsmall="100" md-flex-small="50" md-flex-medium="50" md-flex-large="33" md-flex-xlarge="33" class="b-r thin-border">
            <ib-project-collaborators :project="project"></ib-project-collaborators>
        </md-layout>
        <md-layout md-column md-gutter md-flex-xsmall="100" md-flex-small="50" md-flex-medium="50" md-flex-large="33" md-flex-xlarge="33">
            <ib-project-tokens :project="project"></ib-project-tokens>
        </md-layout>
        <md-layout md-column md-gutter md-flex-xsmall="100" md-flex-small="100" md-flex-medium="100" md-flex-large="100" md-flex-xlarge="100">
            <ib-project-cronjobs :project="project"></ib-project-cronjobs>
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

export default {
    props: ['project'],
    components: {
        'ib-project-secrets': ProjectSecrets,
        'ib-project-tokens': ProjectTokens,
        'ib-project-collaborators': ProjectCollaborators,
        'ib-project-badges': ProjectBadges,
        'ib-project-cronjobs': ProjectCronJobs
    }
}
</script>

<style scoped>

</style>
