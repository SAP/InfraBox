export default class User {
    constructor (username, avatarUrl, name, email, githubId) {
        this.githubRepos = []
        this.username = username
        this.avatarUrl = avatarUrl
        this.name = name
        this.email = email
        this.githubId = githubId
    }

    hasGithubAccount () {
        return this.githubId != null
    }
}
