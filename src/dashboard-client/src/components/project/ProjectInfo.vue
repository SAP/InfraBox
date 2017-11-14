<template>
    <md-list-item class="bg-white">
        <md-icon>info</md-icon>
        <span>Project Information</span>

        <md-list-expand>
            <md-list class="m-t-md m-b-md">
                <md-list-item class="md-inset m-r-xl">
                    <span class="md-body-2"><i class="fa fa-id-card-o fa-fw p-r-xl" aria-hidden="true"></i>
                    Project ID</span>
                    <span class="md-list-action">
                        {{ project.id }}
                    </span>
                </md-list-item>
            </md-list>
        </md-list-expand>
    </md-list-item>
</template>

<script>

export default {
    props: ['project']
}
</script>
