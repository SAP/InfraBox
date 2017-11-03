<template>
    <div>
        <div v-if="build.commit && build.commit.tag">
            <a target="_blank" :href="b.commit.url">
                <md-icon md-src="../../../static/tag.svg"></md-icon>
                <md-tooltip>Tag</md-tooltip>
            </a>
        </div>
        <div v-if="build.commit && !build.commit.tag && !build.pull_request">
            <a target="_blank" :href="build.commit.url">
                <md-icon md-src="../../../static/git-commit.svg"></md-icon>
                <md-tooltip>Commit</md-tooltip>
            </a>
        </div>
        <div v-if="build.pull_request">
            <a target="_blank" :href="build.pull_request.url">
                <md-icon md-src="../../../static/git-pull-request.svg"></md-icon>
                <md-tooltip>Pull request</md-tooltip>
            </a>
        </div>
    </div>
</template>

<script>

export default {
    props: ['build']
}
</script>
