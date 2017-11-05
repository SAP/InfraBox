import { InternalError, BadRequest } from "./status";
import { config } from "../config/config";

const request = require("request");
const api_url = config.github.api_url;

export function getEmail(token: string) {
    const options = {
        uri: api_url + '/user/emails',
        method: 'GET',
        headers: {
            "Authorization": "token " + token,
            "User-Agent": "InfraBox"
        }
    };

    return new Promise((resolve, reject) => {
        request(options, (err, response, body) => {
            if (err) {
                return reject(new InternalError(err));
            }

            if (response.statusCode !== 200) {
                return reject(new InternalError(body));
            }
            try {
                const r = JSON.parse(body);
                for (const e of r) {
                    if (e.primary && e.verified) {
                        resolve(e.email);
                    }
                }

                return resolve(null);
            } catch (e) {
                reject(e);
            }
        });
    });
}

export function getRepos(token: string) {
    const options = {
        uri: api_url + '/user/repos?visibility=all',
        method: 'GET',
        headers: {
            "Authorization": "token " + token,
            "User-Agent": "InfraBox"
        }
    };

    return new Promise((resolve, reject) => {
        if (!token) {
            return resolve([]);
        }

        request(options, (err, response, body) => {
            if (err) {
                return reject(new InternalError(err));
            }

            if (response.statusCode !== 200) {
                return reject(new InternalError(body));
            }

            return resolve(JSON.parse(body));
        });
    });
}

export function getRepo(token: string, repo: string, owner: string) {
    const options = {
        uri: api_url + '/repos/' + owner + '/' + repo,
        method: 'GET',
        headers: {
            "Authorization": "token " + token,
            "User-Agent": "InfraBox"
        }
    };

    return new Promise((resolve, reject) => {
        request(options, (err, response, body) => {
            if (err) {
                return reject(new InternalError(err));
            }

            if (response.statusCode !== 200) {
                return reject(new InternalError(body));
            }

            return resolve(JSON.parse(body));
        });
    });
}

export function deleteHook(token: string, repo: string, owner: string, id: string) {
    const options = {
        uri: api_url + '/repos/' + owner + '/' + repo + '/hooks/' + id,
        method: 'DELETE',
        headers: {
            "Authorization": "token " + token,
            "User-Agent": "InfraBox"
        }
    };

    return new Promise((resolve, reject) => {
        request(options, (err, response, body) => {
            if (err) {
                return reject(new InternalError(err));
            }

            if (response.statusCode !== 201) {
                try {
                    return reject(new BadRequest(body['errors'][0]['message']));
                } catch (e) {
                    return reject(new InternalError(body));
                }
            }

            return resolve(body);
        });
    });
}

export function createHook(token: string, repo: string, owner: string) {
    const options = {
        uri: api_url + '/repos/' + owner + '/' + repo + '/hooks',
        method: 'POST',
        headers: {
            "Authorization": "token " + token,
            "User-Agent": "InfraBox"
        },
        json: {
            name: "web",
            active: true,
            events: [
                "create", "delete", "public", "pull_request", "push"
            ],
            config: {
                url: config.root_url + '/github/hook',
                content_type: "json",
                secret: config.github.webhook_secret
            }
        }
    };

    return new Promise((resolve, reject) => {
        request(options, (err, response, body) => {
            if (err) {
                return reject(new InternalError(err));
            }

            if (response.statusCode !== 201) {
                try {
                    return reject(new BadRequest(body['errors'][0]['message']));
                } catch (e) {
                    return reject(new InternalError(body));
                }
            }

            return resolve(body);
        });
    });
}

export function createDeployKey(token: string, repo: string, owner: string, key) {
    const options = {
        uri: api_url + '/repos/' + owner + '/' + repo + '/keys',
        method: 'POST',
        headers: {
            "Authorization": "token " + token,
            "User-Agent": "InfraBox"
        },
        json: {
            title: "InfraBox Key",
            key: key.pubKey,
            read_only: true
        }
    };

    return new Promise((resolve, reject) => {
        request(options, (err, response, body) => {
            if (err) {
                return reject(new InternalError(err));
            }

            if (response.statusCode !== 201) {
                return reject(new InternalError(body));
            }

            return resolve();
        });
    });
}
