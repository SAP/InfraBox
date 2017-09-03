"use strict";
const status_1 = require("./status");
const config_1 = require("../config/config");
const request = require("request");
function getCommits(token, url) {
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
                return reject(new status_1.InternalError(err));
            }
            resolve(body);
        });
    });
}
exports.getCommits = getCommits;
function setStatus(token, url, state) {
    const options = {
        uri: url,
        method: 'POST',
        headers: {
            "Authorization": "token " + token,
            "User-Agent": "InfraBox"
        },
        json: {
            state: state,
            target_url: config_1.config.api.url,
            description: "InfraBox",
            context: "Job: Create Jobs"
        }
    };
    return new Promise((resolve, reject) => {
        request(options, (err, response, body) => {
            if (err) {
                return reject(new status_1.InternalError(err));
            }
            if (response.statusCode !== 201) {
                return reject(new status_1.InternalError(body));
            }
            resolve(body);
        });
    });
}
exports.setStatus = setStatus;
