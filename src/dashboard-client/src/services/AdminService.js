import store from '../store'
import NewAPIService from '../services/NewAPIService'

class AdminService {
    loadProjects () {
        return NewAPIService.get(`admin/projects/`)
            .then((s) => {
                store.commit('setAdminProjects', s)
            })
    }

    loadUsers () {
        return NewAPIService.get(`admin/users/`)
            .then((s) => {
                store.commit('setAdminUsers', s)
            })
    }
}

export default new AdminService()
