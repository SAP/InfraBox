<!--
<template>
    <md-card class="main-card">
    	<md-card-header class="main-card-header fix-padding">
			<md-card-header-text>
				<h3 class="md-title card-title">
					<md-layout>
						<md-layout md-vertical-align="center">Quotas</md-layout>
					</md-layout>
				</h3>
			</md-card-header-text>
		</md-card-header>
            <md-card class="clean-card">
                <md-card-area>
                        <md-list class="m-t-md m-b-md">
                            <md-list-item>
                                <md-input-container class="m-r-sm">
                                    <label>Quota Name</label>
                                    <md-input v-model="name" required></md-input>
                                </md-input-container>
                                <md-input-container class="m-l-sm">
                                    <label>Quota Value</label>
                                    <md-textarea v-model="value" required></md-textarea>
                                </md-input-container>
                                <md-input-container class="m-l-sm">
                                    <label>Description</label>
                                    <md-textarea v-model="description"></md-textarea>
                                </md-input-container>
                                <md-input-container class="m-l-sm">
                                    <label>Object ID</label>
                                    <md-textarea v-model="object_id"></md-textarea>
                                </md-input-container>
                                <md-button class="md-icon-button md-list-action" @click="addQuota()">
                                    <md-icon md-theme="running" class="md-primary">add_circle</md-icon>
                                    <md-tooltip>Add new Quota</md-tooltip>
                                </md-button>
                            </md-list-item>
                            <!-- ->
                <md-card-header>
                    <md-card-header-text class="setting-list">
                        <md-icon>security</md-icon>
                        <span>Projects</span>
                    </md-card-header-text>
                </md-card-header>
                            <md-list-item v-for="quota in quotas" :key="quota.id">
                                <div class="md-list-text-container">
                                    {{ quota.name }}
                                </div>
                                <div class="md-list-text-container">
                                    {{ quota.value }}
                                </div>
                                <div class="md-list-text-container">
                                    {{ quota.description }}
                                </div>
                                <div class="md-list-text-container">
                                    {{ quota.object_id }}
                                </div>
                                <div v-if="!quota.object_id.startsWith('default_value')">
                                    <md-button type="submit" class="md-icon-button md-list-action" @click="deleteQuota(quota.id)">
                                        <md-icon class="md-primary">delete</md-icon>
                                        <md-tooltip>Delete Quota permanently</md-tooltip>
                                    </md-button>
                                </div>
                            </md-list-item>
                            <!-- ->
                            <!-- ->
                                        <md-card-header>
                <md-card-header-text class="setting-list">
                    <md-icon>security</md-icon>
                    <span>Users</span>
                </md-card-header-text>
            </md-card-header>
                                        <md-list-item>
                                <md-input-container class="m-r-sm">
                                    <label>Quota Name</label>
                                    <md-input v-model="name" required></md-input>
                                </md-input-container>
                                <md-input-container class="m-l-sm">
                                    <label>Quota Value</label>
                                    <md-textarea v-model="value" required></md-textarea>
                                </md-input-container>
                                <md-input-container class="m-l-sm">
                                    <label>Description</label>
                                    <md-textarea v-model="description"></md-textarea>
                                </md-input-container>
                                <md-input-container class="m-l-sm">
                                    <label>Object ID</label>
                                    <md-textarea v-model="object_id"></md-textarea>
                                </md-input-container>
                                <md-button class="md-icon-button md-list-action" @click="addQuota()">
                                    <md-icon md-theme="running" class="md-primary">add_circle</md-icon>
                                    <md-tooltip>Add new Quota</md-tooltip>
                                </md-button>
                            </md-list-item>
                            <md-list-item v-for="quota in quotas_users" :key="quota.id">
                                <div class="md-list-text-container">
                                    {{ quota.name }}
                                </div>
                                <div class="md-list-text-container">
                                    {{ quota.value }}
                                </div>
                                <div class="md-list-text-container">
                                    {{ quota.description }}
                                </div>
                                <div class="md-list-text-container">
                                    {{ quota.object_id }}
                                </div>
                                <div v-if="!quota.object_id.startsWith('default_value')">
                                    <md-button type="submit" class="md-icon-button md-list-action" @click="deleteQuota(quota.id)">
                                        <md-icon class="md-primary">delete</md-icon>
                                        <md-tooltip>Delete Quota permanently</md-tooltip>
                                    </md-button>
                                </div>
                            </md-list-item>
                            <!-- ->
                        </md-list>
                </md-card-area>
            </md-card>
    </md-card>
</template>
<!-- -->

<template>
    <div>
        <div>
            <quotas-list-users Quotatype="user"></quotas-list-users>
        </div>
        <div>
            <quotas-list-users Quotatype="project"></quotas-list-users>
        </div>
    </div>
</template>



<script>

import QuotasList from './QuotasList'

export default {
    props: ['admin'],
    components: {
        'quotas-list-users': QuotasList
    }

}
</script>

<style scoped>
.fix-padding {
    padding-top: 7px !important;
    padding-bottom: 22px !important;
    padding-left: 0 !important;
}

</style>