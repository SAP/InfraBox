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

		<md-table-card class="clean-card">
			<md-table>
				<md-table-header>
					<md-table-row>
						<md-table-head>Name</md-table-head>
						<md-table-head>Username</md-table-head>
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
                            {{ u.email }}
						</md-table-cell>
					</md-table-row>
				</md-table-body>
			</md-table>

			<md-table-pagination
			:md-size="size"
			:md-total="total"
			:md-page="page"
			md-label="Projects"
			md-separator="of"
			:md-page-options="[20, 50]"
			@pagination="onPagination"></md-table-pagination>
		</md-table-card>
	</md-card>
</template>

<script>
import store from '../../store'
import AdminService from '../../services/AdminService'

export default {
    name: 'AdminProejcts',
    store,
    data: () => {
        return {
            users: [],
            page: 1,
            size: 20,
            total: 0
        }
    },
    created () {
        AdminService.loadUsers().then(() => {
            this.onPagination({ size: this.size, page: this.page })
            this.total = store.state.admin.users.length
        })
    },
    methods: {
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

