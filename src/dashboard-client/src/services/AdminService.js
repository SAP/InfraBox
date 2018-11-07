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

    loadQuotas (Quotatype) {
        return NewAPIService.get(`admin/quotas/${Quotatype}`)
        .then((s) => {
            store.commit('setAdminQuotas', s)
        })
        .catch((err) => {
            NotificationService.$emit('NOTIFICATION', new Notification(err))
        })
    }

    loadQuotasUsers (id) {
        return NewAPIService.get(`admin/quotas/users/${id}`)
        .then((s) => {
            store.commit('setAdminQuotasUsers', s)
        })
        .catch((err) => {
            NotificationService.$emit('NOTIFICATION', new Notification(err))
        })
    }

    loadObjectsID (Quotatype) {
        return NewAPIService.get(`admin/quotas/objects_id/${Quotatype}`)
        .then((s) => {
            store.commit('setAdminObjectsID', s)
        })
        .catch((err) => {
            NotificationService.$emit('NOTIFICATION', new Notification(err))
        })
    }
}

export default new AdminService()
