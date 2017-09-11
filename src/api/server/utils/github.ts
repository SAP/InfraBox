import { InternalError, BadRequest } from "./status";
import { config } from "../config/config";

const request = require("request");

export function getCommits(token: string, url: string) {
    const options = {
        uri: url,
        headers: {
            "Authorization": "token " + token,
            "User-Agent": "InfraBox"
        },
        json: true
    };

    return new Promise((resolve, reject) => {
        request(options, (err, response, body) => {
            if (err) {
                return reject(new InternalError(err));
            }

            resolve(body);
        });
    });
}

export function setStatus(token: string, url: string, state: string, project_id: string, build_id: string) {
    let target_url = config.api.url;
    if (project_id && build_id) {
        target_url += `/dashboard/project/${project_id}/build/${build_id}`;
    }

    const options = {
        uri: url,
        method: 'POST',
        headers: {
            "Authorization": "token " + token,
            "User-Agent": "InfraBox"
        },
        json: {
            state: state,
            target_url: target_url,
            description: "InfraBox",
            context: "Job: Create Jobs"
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

            resolve(body);
        });
    });
}
