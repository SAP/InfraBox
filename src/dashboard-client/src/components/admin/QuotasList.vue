<template>
    <md-card>
        <md-card-header>
                <md-card-header-text class="setting-list">
                    <md-icon>security</md-icon>
                    <span>{{this.Quotatype}}</span>
                </md-card-header-text>
        </md-card-header>
        <md-card-area>
            <md-list-item>
                <!-- Input for new quota -->
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
                    <div class="md-list-text-container">
                        <span>
                            <md-input-container>
                                <label for="object_id">Object ID</label>
                                    <md-select name="Object" id="quota_select" v-model="object_id">
                                        <md-option ref="object_id" v-for="r in objects_id" :value=r.id :key="r.id" class="bg-white">{{r.name}}</md-option>
                                    </md-select>
                            </md-input-container>
                        </span>
                    </div>
                </md-input-container>
                <md-button class="md-icon-button md-list-action" @click="addQuota()">
                    <md-icon md-theme="running" class="md-primary">add_circle</md-icon>
                    <md-tooltip>Add new Quota</md-tooltip>
                </md-button>
            </md-list-item>
            <!-- Quotas list -->
            <md-list-item v-for="quota in quotas" :key="quota.id">
                <div class="md-list-text-container">
                    {{ quota.name }}
                </div>
                <div class="md-list-text-container">
                    <md-input-container class="m-r-sm">
                        <md-input type="number" :name="'newValue_' + quota.id + ''" :value="quota.value"></md-input>
                    </md-input-container>
                </div>
                <div class="md-list-text-container">
                    <md-input-container :name="'newDescription_' + quota.id + ''">
                        <md-textarea type="text" :value="quota.description"></md-textarea>
                    </md-input-container>
                </div>
                <div class="md-list-text-container">
                    {{ quota.object_id }}
                </div>
                <div class="md-list-text-container">
                    <md-button class="md-icon-button md-dense" @click="updateQuota(quota.id)">
                        <md-icon>cached</md-icon>
                    </md-button>
                </div>
                <div v-if="!quota.object_id.startsWith('default_value')">
                    <md-button type="submit" class="md-icon-button md-list-action" @click="deleteQuota(quota.id)">
                        <md-icon class="md-primary">delete</md-icon>
                        <md-tooltip>Delete Quota permanently</md-tooltip>
                    </md-button>
                </div>
            </md-list-item>
        </md-card-area>
    </md-card>
</template>

<script>

import NewAPIService from '../../services/NewAPIService'
import NotificationService from '../../services/NotificationService'
import Notification from '../../models/Notification'
import store from '../../store'
import AdminService from '../../services/AdminService'

export default {
    name: 'AdminProejcts',
    props: ['Quotatype'],
    store,
    data: () => ({
        quotas: [],
        quotas_users: [],
        name: '',
        value: '',
        description: '',
        object_id: '',
        objects_id: [],
        page: 1,
        size: 20,
        total: 0
    }),
    created () {
        this._reloadQuotas()
        this._reloadObjectsID()
        // this._reloadQuotasUser()
    },
    methods: {
        _loadQuotas () {
            if (this.quotas) {
                return
            }

            this._reloadQuotas()
            // this._reloadQuotasUser('00000000-0000-0000-0000-000000000000')
        },
        _reloadQuotas () {
            return AdminService.loadQuotas(this.Quotatype).then(() => {
                this.quotas = store.state.admin.quotas
            })
        },
        _reloadQuotasUser (id) {
            return AdminService.loadQuotasUsers(id).then(() => {
                this.quotas_users = store.state.admin.quotas_users
            })
        },
        _reloadObjectsID () {
            return AdminService.loadObjectsID(this.Quotatype).then(() => {
                this.objects_id = store.state.admin.objects_id
            })
        },
        deleteQuota (id) {
            NewAPIService.delete(`admin/quota/${id}`)
            .then((response) => {
                NotificationService.$emit('NOTIFICATION', new Notification(response))
                this._reloadQuotas()
            })
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
        },
        addQuota () {
            const d = { name: this.name, value: this.value, description: this.description, object_id: this.object_id }
            NewAPIService.post(`admin/quotas/${this.Quotatype}`, d)
            .then((response) => {
                NotificationService.$emit('NOTIFICATION', new Notification(response))
                this.name = ''
                this.value = ''
                this._reloadQuotas()
            })
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
        },
        updateQuota (quotaID) {
            var nameNewValue = 'newValue_' + String(quotaID)
            var newValue = document.getElementsByName(nameNewValue)[0].value
            var nameNewDescription = 'newDescription_' + String(quotaID)
            var newDescription = document.getElementsByName(nameNewDescription)[0].children[0].value

            const d = {value: newValue, description: newDescription}

            NewAPIService.post(`admin/quota/${quotaID}`, d)
            .then((response) => {
                NotificationService.$emit('NOTIFICATION', new Notification(response))
                this._reloadQuotas()
            })
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
        }
    }
}
</script>