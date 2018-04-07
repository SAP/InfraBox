export default class User {
    constructor (username, avatarUrl, name, email, githubId, id) {
        this.githubRepos = []
        this.username = username
        this.avatarUrl = avatarUrl
        this.name = name
        this.email = email
        this.githubId = githubId
        this.id = id
    }

    hasGithubAccount () {
        return this.githubId != null
    }

    isAdmin () {
        return this.id === '00000000-0000-0000-0000-000000000000'
    }
}
