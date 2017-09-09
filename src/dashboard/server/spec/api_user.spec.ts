import { createServer, stopServer } from "../server";
import { insertData } from "../db";
import { getToken } from "./utils";
import { config } from "../../server/config/config";

const request = require("supertest");
const jwt = require("jsonwebtoken");

describe('/api/dashboard/user', function() {
    this.timeout(10000);
    before(insertData({
        user: [{
            id: "ee267114-ec67-4800-853c-ec1325d977fb",
            github_id: 1,
            username: "user",
            avatar_url: "no",
            name: "name"
        }]
    }));

    let server;
    before(() => {
        server = createServer(false);
    });

    after(() => {
        stopServer(server);
    });

    it('should return 401 if no auth token is set', (done) => {
        request(server)
            .get('/api/dashboard/user')
            .expect(401, done);
    });

    it('should return 401 if auth token is invalid', (done) => {
        request(server)
            .get('/api/dashboard/user')
            .set('Cookie', ['token=some weird value'])
            .expect(401, done);
    });

    it('should return 401 if auth token has been expired', (done) => {
        const older_token = jwt.sign({
            user: 'some id', iat: Math.floor(Date.now() / 1000) - 60 * 60 * 24 * 7
        },
            config.dashboard.secret, { expiresIn: "1d" }
        );

        request(server)
            .get('/api/dashboard/user')
            .set('Cookie', ['token=' + older_token])
            .expect(401, done);
    });

    it('should return 401 for an invalid uuid', (done) => {
        const token = getToken("some id");
        request(server)
            .get('/api/dashboard/user')
            .set('Cookie', ['token=' + token])
            .expect(401, done);
    });

    it('should return 401 if user is not found', (done) => {
        const token = getToken('1e267114-ec67-4800-853c-ec1325d977fb');
        request(server)
            .get('/api/dashboard/user')
            .set('Cookie', ['token=' + token])
            .expect(401, done);
    });

    it('should return 200 and user data if token is valid', (done) => {
        const token = getToken('ee267114-ec67-4800-853c-ec1325d977fb');
        request(server)
            .get('/api/dashboard/user')
            .set('Cookie', ['token=' + token])
            .expect(200, done);
    });
});
