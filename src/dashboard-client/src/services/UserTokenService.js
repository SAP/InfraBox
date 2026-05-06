import NewAPIService from './NewAPIService'
import NotificationService from './NotificationService'
import Notification from '../models/Notification'

class UserTokenService {
    loadTokens () {
        return NewAPIService.get('user/global-tokens')
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
                throw err
            })
    }

    createToken (description, scopePush, scopePull) {
        return NewAPIService.post('user/global-tokens', {
            description,
            scope_push: scopePush,
            scope_pull: scopePull
        }).catch((err) => {
            NotificationService.$emit('NOTIFICATION', new Notification(err))
            throw err
        })
    }

    deleteToken (tokenId) {
        return NewAPIService.delete(`user/global-tokens/${tokenId}`)
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
                throw err
            })
    }

    loadAccessLog (tokenId) {
        return NewAPIService.get(`user/global-tokens/${tokenId}/access-log`)
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
                throw err
            })
    }
}

export default new UserTokenService()
