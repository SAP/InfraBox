<template>
    <div>
        <ib-project-secrets :project="project"></ib-project-secrets>
        <ib-project-collaborators :project="project"></ib-project-collaborators>
        <ib-project-tokens :project="project"></ib-project-tokens>
        <ib-project-info :project="project"></ib-project-info>
        <ib-project-badges :project="project"></ib-project-badges>
    </div>
</template>

<script>
import ProjectSecrets from './Secrets'
import ProjectTokens from './Tokens'
import ProjectCollaborators from './Collaborators'
import ProjectInfo from './ProjectInfo'
import ProjectBadges from './Badges'

export default {
    props: ['project'],
    components: {
        'ib-project-secrets': ProjectSecrets,
        'ib-project-tokens': ProjectTokens,
        'ib-project-collaborators': ProjectCollaborators,
        'ib-project-info': ProjectInfo,
        'ib-project-badges': ProjectBadges
    }
}
</script>

<style scoped>

</style>
