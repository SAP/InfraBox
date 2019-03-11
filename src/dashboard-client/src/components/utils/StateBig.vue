<template>
<div>
<div v-if="state=='queued'" class="state-widget bg-neutral">
    <i class="fas fa-pause-circle-o fa-4x"></i>
    <h1 class="m-xs">QUEUED</h1>
</div>

<div v-if="state=='scheduled'" class="state-widget bg-neutral">
    <i class="fas fa-th-list fa-4x"></i>
    <h1 class="m-xs">SCHEDULED</h1>
</div>

<div v-if="state=='running'" class="state-widget bg-running">
    <i class="fas fa-dot-circle-o fa-4x"></i>
    <h1 class="m-xs">RUNNING</h1>
</div>

<div v-if="state=='finished' || state=='ok'" class="state-widget bg-success">
    <i class="fas fa-check fa-4x"></i>
    <h1 class="m-xs">OK</h1>
</div>

<div v-if="state=='skipped'" class="state-widget bg-neutral">
    <i class="fas fa-share fa-4x"></i>
    <h1 class="m-xs">SKIPPED</h1>
</div>

<div v-if="state=='unstable'" class="state-widget bg-unstable">
    <i class="fas fa-bolt fa-4x"></i>
    <h1 class="m-xs">UNSTABLE</h1>
</div>

<div v-if="state=='failure'" class="state-widget bg-failure">
    <i class="fas fa-bolt fa-4x"></i>
    <h1 class="m-xs">FAILURE</h1>
</div>

<div v-if="state=='error'" class="state-widget bg-error">
    <i class="fas fa-bomb fa-4x"></i>
    <h1 class="m-xs">ERROR</h1>
</div>

<div v-if="state=='killed'" class="state-widget bg-error">
    <i class="fas fa-ban fa-4x"></i>
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
</style>
