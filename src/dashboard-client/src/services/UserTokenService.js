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

    createToken (description, scopePush, scopePull, expiresDays) {
        return NewAPIService.post('user/global-tokens', {
            description,
            scope_push: scopePush,
            scope_pull: scopePull,
            expires_days: expiresDays || 365
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
    // MCP token methods — /api/v1/mcp/tokens/*

    loadMcpTokens () {
        return NewAPIService.get('mcp/tokens/')
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
                throw err
            })
    }

    createMcpToken (name, enabledProjects, expiresDays) {
        return NewAPIService.post('mcp/tokens/', {
            name,
            enabled_projects: enabledProjects || {},
            expires_days: expiresDays || 365
        }).catch((err) => {
            NotificationService.$emit('NOTIFICATION', new Notification(err))
            throw err
        })
    }

    revokeMcpToken (tokenId) {
        return NewAPIService.delete(`mcp/tokens/${tokenId}`)
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
                throw err
            })
    }

    setMcpTrigger (tokenId, allow) {
        const method = allow ? 'post' : 'delete'
        return NewAPIService[method](`mcp/tokens/${tokenId}/trigger`, {})
            .catch((err) => {
                NotificationService.$emit('NOTIFICATION', new Notification(err))
                throw err
            })
    }
}

export default new UserTokenService()
