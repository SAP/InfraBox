<template>
<div>
<div v-if="state=='queued'" class="state-widget bb-bg-neutral">
    <i class="fa fa-pause-circle-o fa-4x"></i>
    <h1 class="m-xs">QUEUED</h1>
</div>

<div v-if="state=='scheduled'" class="state-widget bb-bg-grey">
    <i class="fa fa-th-list fa-4x"></i>
    <h1 class="m-xs">SCHEDULED</h1>
</div>

<div v-if="state=='running'" class="state-widget bb-bg-running">
    <i class="fa fa-dot-circle-o fa-4x"></i>
    <h1 class="m-xs">RUNNING</h1>
</div>

<div v-if="state=='finished'" class="state-widget bb-bg-success">
    <i class="fa fa-check fa-4x"></i>
    <h1 class="m-xs">OK</h1>
</div>

<div v-if="state=='skipped'" class="state-widget bb-bg-grey">
    <i class="fa fa-share fa-4x"></i>
    <h1 class="m-xs">SKIPPED</h1>
</div>

<div v-if="state=='failure'" class="state-widget bb-bg-failure">
    <i class="fa fa-bolt fa-4x"></i>
    <h1 class="m-xs">FAILURE</h1>
</div>

<div v-if="state=='error'" class="state-widget bb-bg-error">
    <i class="fa fa-bomb fa-4x"></i>
    <h1 class="m-xs">ERROR</h1>
</div>

<div v-if="state=='killed'" class="state-widget bb-bg-grey">
    <i class="fa fa-ban fa-4x"></i>
    <h1 class="m-xs">KILLED</h1>
</div>
</div>
</template>

<script>
export default {
    props: ['state']
}
</script>

<style scoped>

.state-widget {
    color: white;
    padding: 10px 0 10px;
    border-radius: 2%;
    text-align: center;
    margin: 5px;
}

.m-xs {
    font-weight: normal;
    margin: 5px;
}

.bb-bg-failure {
    background-color: #cc5965;
}

.bb-bg-success {
    background-color: #1ab394;
}
</style>
