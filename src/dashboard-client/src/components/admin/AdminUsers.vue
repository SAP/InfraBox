<template>
    <md-card class="main-card">
        <md-card-header class="main-card-header fix-padding">
            <md-card-header-text>
                <h3 class="md-title card-title">
                    <md-layout>
                        <md-layout md-vertical-align="center">Users</md-layout>
                    </md-layout>
                </h3>
            </md-card-header-text>
        </md-card-header>

    <md-card md-theme="white" class="full-height clean-card">
            <md-card-area>
                <md-list class="m-t-md m-b-md">
                    <md-list-item>
                        <md-input-container class="m-r-sm">
                            <label>Name</label>
                            <md-input v-model="form.name"></md-input>
                        </md-input-container>
                        <md-input-container class="m-r-sm">
                            <label>Username</label>
                            <md-input v-model="form.username"></md-input>
                        </md-input-container>
                        <md-input-container class="m-r-sm">
                            <label>Email</label>
                            <md-input v-model="form.email"></md-input>
                        </md-input-container>
                        <md-input-container>
                            <label>Role</label>
                            <md-select name="role" id="role" v-model="form.role">
                                <md-option value="" class="bg-white">Any</md-option>
                                <md-option value="user" class="bg-white">user</md-option>
                                <md-option value="devops" class="bg-white">devops</md-option>
                                <md-option value="admin" class="bg-white">admin</md-option>
                            </md-select>
                        </md-input-container>
                        <md-button class="md-icon-button md-list-action" @click="doSearch()">
                            <md-icon md-theme="running" class="md-primary">search</md-icon>
                            <md-tooltip>Search</md-tooltip>
                        </md-button>
                        <md-button class="md-icon-button md-list-action" @click="resetSearch()">
                            <md-icon md-theme="running" class="md-primary">clear</md-icon>
                            <md-tooltip>Clear</md-tooltip>
                        </md-button>
                    </md-list-item>
                </md-list>
            </md-card-area>
        </md-card>

        <md-table-card class="clean-card">
            <md-table>
                <md-table-header>
                    <md-table-row>
                        <md-table-head>Name</md-table-head>
                        <md-table-head>User</md-table-head>
                        <md-table-head>Role</md-table-head>
                        <md-table-head>Email</md-table-head>
                    </md-table-row>
                </md-table-header>
                <md-table-body>
                    <md-table-row v-for="u in users" :key="u.id">
                        <md-table-cell>
                            <img :src="u.avatar_url" /> {{ u.name }}
                        </md-table-cell>
                        <md-table-cell>
                            {{ u.username }}
                        </md-table-cell>
                        <md-table-cell>
                            <md-select v-model="u.role" name="role" id="u.id" v-on:change="setUserRole(u.id, $event)" :disabled="!isAdmin()">
                                <md-option value="user">User</md-option>
                                <md-option value="devops">Devops</md-option>
                                <md-option value="admin">Admin</md-option>
                            </md-select>
                        </md-table-cell>
                        <md-table-cell>
                            {{ u.email }}
                        </md-table-cell>
                    </md-table-row>
                </md-table-body>
            </md-table>

            <md-table-pagination v-if="!this.search.search"
                :md-size="size"
                :md-total="total"
                :md-page="page"
                md-label="Users"
                md-separator="of"
                :md-page-options="[20, 50]"
            @pagination="onPagination">
            </md-table-pagination>
        </md-table-card>
    </md-card>
</template>

<script>
import store from '../../store'
import AdminService from '../../services/AdminService'
import NotificationService from '../../services/NotificationService'
import Notification from '../../models/Notification'

export default {
    name: 'AdminUsers',
    store,
    data: () => {
        return {
            users: [],
            roles: {},
            page: 1,
            size: 20,
            total: 0,

            form: {
                name: null,
                username: null,
                email: null,
                role: null
            },

            search: {
                name: null,
                username: null,
                email: null,
                role: null,
                search: false
            }
        }
    },

    created () {
        AdminService.loadUsers().then(() => {
            for (let u of store.state.admin.users) {
                this.roles[u.id] = u.role
            }
            this.users = store.state.admin.users
            this.total = store.state.admin.users.length
            this.onPagination({ size: this.size, page: this.page })
        })
    },

    methods: {
        isAdmin () {
            return store.state.user.isAdmin()
        },

        setUserRole (id, role) {
            if (role === this.roles[id]) {
                return
            }
            console.log(id, role)
            const user = this.users.find(c => c.id === id)
            AdminService.setUserRole(id, role).then(() => {
                this.roles[id] = role
                NotificationService.$emit('NOTIFICATION', new Notification({ message: `user ${user.name} role is set to ${role}` }))
            }).catch((err) => {
                user.role = this.roles[id]
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
        },

        resetSearch () {
            this.search.search = false
            this.users = store.state.admin.users
        },

        searchUsers () {
            if (store.state.admin.users.length === 0) {
                return []
            }

            let users = []

            for (let u of store.state.admin.users) {
                if (!this.search.search) {
                    users.push(u)
                    continue
                }

                if (this.search.name && u.name.toLowerCase().search(this.search.name.toLowerCase()) === -1) {
                    continue
                }

                if (this.search.username && u.username.toLowerCase().search(this.search.username.toLowerCase()) === -1) {
                    continue
                }

                if (this.search.email && u.email.toLowerCase().search(this.search.email.toLowerCase()) === -1) {
                    continue
                }

                if (this.search.role && u.role !== this.search.role) {
                    continue
                }

                users.push(u)
            }

            return users
        },

        doSearch () {
            this.search = {
                username: this.form.username,
                name: this.form.name,
                role: this.form.role,
                email: this.form.email,
                search: true
            }

            this.users = this.searchUsers()
        },

        onPagination (opt) {
            if (this.size !== opt.size) {
                this.page = 1
            } else {
                this.page = opt.page
            }

            this.size = opt.size

            const p = this.page - 1
            const s = p * this.size
            const e = s + this.size

            this.users = store.state.admin.users.slice(s, e)
        }
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

