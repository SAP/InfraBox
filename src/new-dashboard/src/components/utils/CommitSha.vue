<template>
    <div>
        {{ sha.substring(0, 8) }}
    </div>
</template>

<script>
export default {
    props: ['sha']
}
</script>
