import store from '../store'
import NewAPIService from '../services/NewAPIService'
import NotificationService from '../services/NotificationService'
import Notification from '../models/Notification'

class AdminService {
    loadProjects () {
        return NewAPIService.get(`admin/projects/`)
            .then((s) => {
                store.commit('setAdminProjects', s)
            })
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
    }

    loadUsers () {
        return NewAPIService.get(`admin/users/`)
            .then((s) => {
                store.commit('setAdminUsers', s)
            })
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
    }

    loadQuotas () {
        return NewAPIService.get(`admin/quotas/`)
        .then((s) => {
            store.commit('setAdminQuotas', s)
        })
        .catch((err) => {
            NotificationService.$emit('NOTIFICATION', new Notification(err))
        })
    }
}

export default new AdminService()
