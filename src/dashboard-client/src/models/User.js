export default class User {
    constructor (username, avatarUrl, name, email, githubId, id, role) {
        this.githubRepos = []
        this.username = username
        this.avatarUrl = avatarUrl
        this.name = name
        this.email = email
        this.githubId = githubId
        this.id = id
        this.role = role
    }

    hasGithubAccount () {
        return this.githubId != null
    }

    isAdmin () {
        return this.role === 'admin'
    }

    hasWriteAccess () {
        return this.role === 'devops' || this.isAdmin()
    }
}
