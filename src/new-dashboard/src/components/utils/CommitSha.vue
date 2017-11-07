<template>
    <div>
        <i class="fa fa-fw fa-github"></i><span> {{ sha.substring(0, 8) }}</span>
    </div>
</template>

<script>
export default {
    props: ['sha']
}
</script>
