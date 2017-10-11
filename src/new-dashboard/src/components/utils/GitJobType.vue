<template>
    <div>
        <div v-if="build.commit && build.commit.tag">
            <a target="_blank" :href="b.commit.url">
                tag
            </a>
        </div>
        <div v-if="build.commit && !build.commit.tag && !build.pull_request">
            <a target="_blank" :href="build.commit.url">
                commit
            </a>
        </div>
        <div v-if="build.pull_request">
            <a target="_blank" :href="build.pull_request.url">
                pr
            </a>
        </div>
    </div>
</template>

<script>

export default {
    props: ['build']
}
</script>
