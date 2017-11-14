<template>
    <div>
        <md-list md-theme="white">
            <ib-project-secrets :project="project"></ib-project-secrets>
            <ib-project-collaborators :project="project"></ib-project-collaborators>
            <ib-project-tokens :project="project"></ib-project-tokens>
            <ib-project-info :project="project"></ib-project-info>
        </md-list>
    </div>
</template>

<script>
import ProjectSecrets from './Secrets'
import ProjectTokens from './Tokens'
import ProjectCollaborators from './Collaborators'
import ProjectInfo from './ProjectInfo'

export default {
    props: ['project'],
    components: {
        'ib-project-secrets': ProjectSecrets,
        'ib-project-tokens': ProjectTokens,
        'ib-project-collaborators': ProjectCollaborators,
        'ib-project-info': ProjectInfo
    }
}
</script>

<style scoped>

</style>
