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

    loadClusters () {
        return NewAPIService.get(`admin/clusters/`)
            .then((s) => {
                store.commit('setAdminClusters', s)
            })
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
    }

    setUserRole (userId, role) {
        const payload = {
            id: userId,
            role: role
        }
        return NewAPIService.post(`admin/users/`, payload)
            .then(() => {
                store.commit('setAdminUserRole', payload)
            })
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
    }

    updateCluster (name, enabled) {
        const payload = {
            name: name,
            enabled: enabled
        }
        return NewAPIService.post(`admin/clusters/`, payload)
            .then(() => {
                store.commit('updateAdminCluster', payload)
            })
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
            })
    }
}

export default new AdminService()
