import { createServer, stopServer } from "../server";
import { db } from "../db";
import { getToken } from "../spec/utils";
import * as _ from "lodash";
let times = require("async/times");

let request = require("supertest");
require("should");

describe('/api/v1/project/:project_id/build/:build_id/job/:job_id/stats/history', () => {
    let server;
    let token = null;
    let user_id = null;
    let build_id = null;
    let job_id = null;
    let repo_id = null;
    before((done) => {
        server = createServer(false);

        db.one(`SELECT u.id user_id, r.id repo_id, b.id build_id, j.id job_id FROM job j
                           INNER JOIN build b
                           ON j.build_id = b.id
                            AND b.build_number > 5
                           INNER JOIN commit c
                           ON c.id = b.commit_id
                           INNER JOIN repository r
                           ON r.id = c.repository_id
                            AND b.repository_id = r.id
                            AND c.repository_id = r.id
                           INNER JOIN collaborator co
                           ON r.id = co.repository_id
                           INNER JOIN "user" u
                           ON co.user_id = u.id
                           LIMIT 1`)
        .then((d) => {
            user_id = d.user_id;
            build_id = d.build_id;
            job_id = d.job_id;
            repo_id = d.repo_id;
            token = getToken(user_id);
            done(null);
        }).catch(done);
    });

    after(() => {
        stopServer(server);
    });

    it('should return 200 and one value', (done) => {
        let num_requests = 1000;
        let start = Date.now();
        times(num_requests, (n, next) => {
            request(server)
                    .get('/api/v1/repository/' + repo_id + '/build/' + build_id + '/job/' + job_id + '/stats/history')
                    .set('auth-token', token)
                    .expect(200, next);
        }, (err) => {
            let end = Date.now();
            let diff = end - start;
            console.log(diff, "ms");
            console.log(num_requests / (diff / 1000), "req/s");
            done(err);
        });
    });
});
