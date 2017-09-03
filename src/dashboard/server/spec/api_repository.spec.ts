import { createServer, stopServer } from "../server";
import { insertData } from "../db";
import { getToken } from "./utils";
import * as _ from "lodash";

const request = require("supertest");
require("should");

describe('/api/dashboard/project', function() {
    this.timeout(10000);

    const data = {
        user: [{
            id: "ee267114-ec67-4800-853c-ec1325d977fb",
            github_id: 1,
            username: "user 1",
            avatar_url: "no",
            email: "user1@infrabox.com",
            name: "name"
        }, {
            id: "b0907c0d-2642-47f4-8a55-eaf70bce8289",
            github_id: 2,
            username: "user 2",
            avatar_url: "no",
            email: "user2@infrabox.com",
            name: "name"
        }],
        project: [{
            id: "41443519-836c-4d8b-890c-8ec76ecbcd5c",
            name: "repo 1",
            type: "github"
        }, {
            id: "c9e039a3-8377-4c4b-a751-22a124f8fbe0",
            name: "repo 2",
            type: "github"
        }],
        collaborator: [
            // User 1 has access to repo 1
            {
                user_id: "ee267114-ec67-4800-853c-ec1325d977fb",
                project_id: "41443519-836c-4d8b-890c-8ec76ecbcd5c",
            },

            // User 2 has access to repo 1 and repo 2
            {
                user_id: "b0907c0d-2642-47f4-8a55-eaf70bce8289",
                project_id: "41443519-836c-4d8b-890c-8ec76ecbcd5c",
            },
            {
                user_id: "b0907c0d-2642-47f4-8a55-eaf70bce8289",
                project_id: "c9e039a3-8377-4c4b-a751-22a124f8fbe0",
            }]
    };

    before(insertData(data));

    let server;
    before(() => {
        server = createServer(false);
    });

    after(() => {
        stopServer(server);
    });

    it('should return 401 if no auth token is set', (done) => {
        request(server)
            .get('/api/dashboard/project')
            .expect(401, done);
    });

    it('should return 200 and repo 1 data for user 1', (done) => {
        const token = getToken("ee267114-ec67-4800-853c-ec1325d977fb");
        request(server)
            .get('/api/dashboard/project')
            .set('auth-token', token)
            .expect(200)
            .expect([{
                id: "41443519-836c-4d8b-890c-8ec76ecbcd5c",
                name: "repo 1",
                type: "github"
            }], done);
    });

    it('should return 200 and repo 1 and repo 2 data for user 2', (done) => {
        let token = getToken("b0907c0d-2642-47f4-8a55-eaf70bce8289");
        request(server)
            .get('/api/dashboard/project')
            .set('auth-token', token)
            .expect(200)
            .expect([{
                id: "41443519-836c-4d8b-890c-8ec76ecbcd5c",
                name: "repo 1",
                type: "github"
            }, {
                id: "c9e039a3-8377-4c4b-a751-22a124f8fbe0",
                name: "repo 2",
                type: "github"
            }], done);
    });
});

describe('/api/dashboard/project/:project_id/collaborators', () => {
    let data = {
        user: [{
            id: "ee267114-ec67-4800-853c-ec1325d977fb",
            github_id: 1,
            username: "user_1",
            avatar_url: "no",
            name: "name",
            email: "user1@infrabox.com"
        }, {
            id: "b0907c0d-2642-47f4-8a55-eaf70bce8289",
            github_id: 2,
            username: "user_2",
            avatar_url: "no",
            name: "name",
            email: "user2@infrabox.com"
        }],
        project: [{
            id: "41443519-836c-4d8b-890c-8ec76ecbcd5c",
            name: "repo 1",
            type: "github"
        }],
        collaborator: [
            // User 1 has access to repo 1
            {
                user_id: "ee267114-ec67-4800-853c-ec1325d977fb",
                project_id: "41443519-836c-4d8b-890c-8ec76ecbcd5c",
                owner: true
            }]
    };

    before(insertData(data));

    let server;
    before(() => {
        server = createServer(false);
    });

    after(() => {
        stopServer(server);
    });

    it('should return 401 if no auth token is set', (done) => {
        request(server)
            .post('/api/dashboard/project/' + data.project[0].id + '/collaborators')
            .expect(401, done);
    });

    it('should return 400 if email is not set', (done) => {
        let token = getToken("ee267114-ec67-4800-853c-ec1325d977fb");
        request(server)
            .post('/api/dashboard/project/' + data.project[0].id + '/collaborators')
            .send({})
            .set('auth-token', token)
            .expect(400, done);
    });

    it('should return 400 if user not found', (done) => {
        let token = getToken("ee267114-ec67-4800-853c-ec1325d977fb");
        request(server)
            .post('/api/dashboard/project/' + data.project[0].id + '/collaborators')
            .send({ username: "some" })
            .set('auth-token', token)
            .expect(400)
            .expect({ message: "user not found", type: "error" }, done);
    });

    // TODO(Steffen): add these tests
    // should return 400 if user already collaborator
    // should return 404 if user has no permissions

    it('should return 200 and successfully add the user', (done) => {
        let token = getToken("ee267114-ec67-4800-853c-ec1325d977fb");
        request(server)
            .post('/api/dashboard/project/' + data.project[0].id + '/collaborators')
            .send({ username: data.user[1].username })
            .set('auth-token', token)
            .expect({ message: "successfully added user", type: "success" })
            .expect(200)
            .end((err) => {
                if (err) {
                    return done(err);
                }

                // check if we also receive it
                request(server)
                    .get('/api/dashboard/project/' + data.project[0].id + '/collaborators')
                    .set('auth-token', token)
                    .expect(200)
                    .expect((res) => {
                        res.body.should.be.instanceof(Array).and.have.lengthOf(2);
                    }).end(done);
            });
    });
});

describe('/api/dashboard/project/:project_id/commit/:commit_id', () => {
    let data = {
        user: [{
            id: "ee267114-ec67-4800-853c-ec1325d977fb",
            github_id: 1,
            username: "user 1",
            avatar_url: "no",
            name: "name"
        }],
        repository: [{
            id: "41443519-836c-4d8b-890c-8ec76ecbcd5c",
            name: "repo 1",
            html_url: "html url",
            clone_url: "ssh url",
            github_id: 1,
            private: false,
            project_id: "51443519-836c-4d8b-890c-8ec76ecbcd5c"
        }],
        project: [{
            id: "51443519-836c-4d8b-890c-8ec76ecbcd5c",
            name: "repo 1",
            type: "github"
        }],
        collaborator: [{
            user_id: "ee267114-ec67-4800-853c-ec1325d977fb",
            project_id: "51443519-836c-4d8b-890c-8ec76ecbcd5c"
        }],
        commit: [{
            id: "ca82a6dff817ec66f44342007202690a93763949",
            message: "message",
            repository_id: "41443519-836c-4d8b-890c-8ec76ecbcd5c",
            timestamp: "2016-09-23T23:51:40.000Z",
            author_name: "author_name",
            author_email: "author_email",
            author_username: "author_username",
            committer_name: "committer_name",
            committer_email: "committer_email",
            committer_username: "committer_username",
            url: "url",
            branch: "master",
            project_id: "51443519-836c-4d8b-890c-8ec76ecbcd5c"
        }]
    };

    before(insertData(data));

    let server;
    before(() => {
        server = createServer(false);
    });

    after(() => {
        stopServer(server);
    });

    it('should return 401 if no auth token is set', (done) => {
        request(server)
            .get('/api/dashboard/project/51443519-836c-4d8b-890c-8ec76ecbcd5c/commit/ca82a6dff817ec66f44342007202690a93763949')
            .expect(401, done);
    });

    it('should return 200 and the commit', (done) => {
        let token = getToken("ee267114-ec67-4800-853c-ec1325d977fb");
        let expect = _.cloneDeep(data.commit[0]);
        expect['added'] = [];
        expect['removed'] = [];
        expect['modified'] = [];

        request(server)
            .get('/api/dashboard/project/51443519-836c-4d8b-890c-8ec76ecbcd5c/commit/ca82a6dff817ec66f44342007202690a93763949')
            .set('auth-token', token)
            .expect(200)
            .expect(expect, done);
    });

    it('should return 404 if ids are wrong', (done) => {
        let token = getToken("ee267114-ec67-4800-853c-ec1325d977fb");
        request(server)
            .get('/api/dashboard/project/41443519-836c-4d8b-890c-8ec76ecbcd5c/commit/ca82a6dff817ec66f44342007202690a93763949')
            .set('auth-token', token)
            .expect(404, done);
    });

    it('should return 404 if ids are invalid', (done) => {
        let token = getToken("ee267114-ec67-4800-853c-ec1325d977fb");
        request(server)
            .get('/api/dashboard/project/41443519-836c-4d8b-890c-8ec76ecbcd5c/commit/;')
            .set('auth-token', token)
            .expect(404, done);
    });
});

describe('/api/dashboard/project/:project_id/job/:job_id/testruns', () => {
    let data = {
        user: [{
            id: "ee267114-ec67-4800-853c-ec1325d977fb",
            github_id: 1,
            username: "user 1",
            avatar_url: "no",
            name: "name"
        }],
        repository: [{
            id: "41443519-836c-4d8b-890c-8ec76ecbcd5c",
            name: "repo 1",
            html_url: "html url",
            clone_url: "ssh url",
            github_id: 1,
            project_id: "51443519-836c-4d8b-890c-8ec76ecbcd5c",
            private: false,
        }],
        project: [{
            id: "51443519-836c-4d8b-890c-8ec76ecbcd5c",
            name: "repo 1",
            type: "github"
        }],
        collaborator: [{
            user_id: "ee267114-ec67-4800-853c-ec1325d977fb",
            project_id: "51443519-836c-4d8b-890c-8ec76ecbcd5c",
        }],
        commit: [{
            id: "ca82a6dff817ec66f44342007202690a93763949",
            message: "message",
            repository_id: "41443519-836c-4d8b-890c-8ec76ecbcd5c",
            timestamp: "2016-09-23T23:51:40.000Z",
            author_name: "author_name",
            author_email: "author_email",
            author_username: "author_username",
            committer_name: "committer_name",
            committer_email: "committer_email",
            committer_username: "committer_username",
            url: "url",
            project_id: "51443519-836c-4d8b-890c-8ec76ecbcd5c",
            branch: "master"
        }],
        build: [{
            id: "3fc256b0-cc24-47ea-84a9-0816d72fabe6",
            project_id: "51443519-836c-4d8b-890c-8ec76ecbcd5c",
            commit_id: "ca82a6dff817ec66f44342007202690a93763949",
            build_number: 1
        }],
        test: [{
            name: "T1",
            id: '2c215611-0a7d-4b3a-8967-ce34ba59df52',
            suite: "S1",
            project_id: "51443519-836c-4d8b-890c-8ec76ecbcd5c",
        }],
        test_run: [{
            test_id: '2c215611-0a7d-4b3a-8967-ce34ba59df52',
            job_id: '2c215611-0a7d-4b3a-8967-ce34ba59df52',
            state: "ok",
            project_id: "51443519-836c-4d8b-890c-8ec76ecbcd5c",
            duration: 12
        }],
        job: [{
            id: '2c215611-0a7d-4b3a-8967-ce34ba59df52',
            state: 'finished',
            build_id: "3fc256b0-cc24-47ea-84a9-0816d72fabe6",
            type: 'run_project_container',
            dockerfile: 'Dockerfile',
            name: 'name',
            build_only: false,
            project_id: "51443519-836c-4d8b-890c-8ec76ecbcd5c",
            cpu: 1,
            memory: 1024
        }]
    };

    before(insertData(data));

    let server;
    before(() => {
        server = createServer(false);
    });

    after(() => {
        stopServer(server);
    });

    it('should return 401 if no auth token is set', (done) => {
        request(server)
            .get('/api/dashboard/project/51443519-836c-4d8b-890c-8ec76ecbcd5c/job/2c215611-0a7d-4b3a-8967-ce34ba59df52/testruns')
            .expect(401, done);
    });

    it('should return 200 and the tests', (done) => {
        let token = getToken("ee267114-ec67-4800-853c-ec1325d977fb");
        request(server)
            .get('/api/dashboard/project/51443519-836c-4d8b-890c-8ec76ecbcd5c/job/2c215611-0a7d-4b3a-8967-ce34ba59df52/testruns')
            .set('auth-token', token)
            .expect(200)
            .expect([{ build_number: 0, state: "ok", name: "T1", suite: "S1", duration: 12, message: null, stack: null }], done);
    });

    it('should return 404 if ids are wrong', (done) => {
        let token = getToken("ee267114-ec67-4800-853c-ec1325d977fb");
        request(server)
            .get('/api/dashboard/project/61443519-836c-4d8b-890c-8ec76ecbcd5c/job/2c215611-0a7d-4b3a-8967-ce34ba59df52/testruns')
            .set('auth-token', token)
            .expect(404, done);
    });
});

describe('/api/dashboard/project/:project_id/job/:job_id/stats/history', () => {
    let data = {
        user: [{
            id: "ee267114-ec67-4800-853c-ec1325d977fb",
            github_id: 1,
            username: "user 1",
            avatar_url: "no",
            name: "name"
        }],
        project: [
            {
                id: "81443519-836c-4d8b-890c-8ec76ecbcd5c",
                name: "repo 1",
                type: "github"
            }, {
                id: "91443519-836c-4d8b-890c-8ec76ecbcd5c",
                name: "repo 2",
                type: "github"
            }],
        repository: [
            {
                id: "41443519-836c-4d8b-890c-8ec76ecbcd5c",
                project_id: "81443519-836c-4d8b-890c-8ec76ecbcd5c",
                name: "repo 1",
                html_url: "html url",
                clone_url: "ssh url",
                github_id: 1,
                private: false,
            }, {
                id: "51443519-836c-4d8b-890c-8ec76ecbcd5c",
                project_id: "91443519-836c-4d8b-890c-8ec76ecbcd5c",
                name: "repo 2",
                html_url: "html url",
                clone_url: "ssh url",
                github_id: 1,
                private: false,
            }],
        collaborator: [{
            user_id: "ee267114-ec67-4800-853c-ec1325d977fb",
            project_id: "81443519-836c-4d8b-890c-8ec76ecbcd5c",
        }],
        commit: [{
            id: "ca82a6dff817ec66f44342007202690a93763949",
            message: "message",
            repository_id: "41443519-836c-4d8b-890c-8ec76ecbcd5c",
            project_id: "81443519-836c-4d8b-890c-8ec76ecbcd5c",
            timestamp: "2016-09-23T23:51:40.000Z",
            author_name: "author_name",
            author_email: "author_email",
            author_username: "author_username",
            committer_name: "committer_name",
            committer_email: "committer_email",
            committer_username: "committer_username",
            url: "url",
            branch: "master"
        }],
        build: [
            // for first repo
            {
                id: "3fc256b0-cc24-47ea-84a9-0816d72fabe6",
                project_id: "81443519-836c-4d8b-890c-8ec76ecbcd5c",
                commit_id: "ca82a6dff817ec66f44342007202690a93763949",
                build_number: 1
            }, {
                id: "4fc256b0-cc24-47ea-84a9-0816d72fabe6",
                project_id: "81443519-836c-4d8b-890c-8ec76ecbcd5c",
                commit_id: "ca82a6dff817ec66f44342007202690a93763949",
                build_number: 2
            },

            // for second repo
            {
                id: "7fc256b0-cc24-47ea-84a9-0816d72fabe6",
                project_id: "91443519-836c-4d8b-890c-8ec76ecbcd5c",
                commit_id: "da82a6dff817ec66f44342007202690a93763949",
                build_number: 1
            }],
        test: [
            // for first repo
            {
                name: "T1",
                id: '2c215611-0a7d-4b3a-8967-ce34ba59df52',
                suite: "S1",
                project_id: "81443519-836c-4d8b-890c-8ec76ecbcd5c",
            },

            // for second repo
            {
                name: "T1 repo 2",
                id: '6c215611-0a7d-4b3a-8967-ce34ba59df52',
                suite: "S1 repo 2",
                project_id: "91443519-836c-4d8b-890c-8ec76ecbcd5c",
        }],
        test_run: [{
            id: '2c215611-0a7d-4b3a-8967-ce34ba59df52',
            test_id: '2c215611-0a7d-4b3a-8967-ce34ba59df52',
            job_id: '2c215611-0a7d-4b3a-8967-ce34ba59df52',
            project_id: "81443519-836c-4d8b-890c-8ec76ecbcd5c",
            duration: 10,
            state: "ok"
        }, {
            id: '3c215611-0a7d-4b3a-8967-ce34ba59df52',
            test_id: '2c215611-0a7d-4b3a-8967-ce34ba59df52',
            job_id: '3c215611-0a7d-4b3a-8967-ce34ba59df52',
            project_id: "81443519-836c-4d8b-890c-8ec76ecbcd5c",
            duration: 20,
            state: "ok",
        }, {
            id: '4c215611-0a7d-4b3a-8967-ce34ba59df52',
            test_id: '6c215611-0a7d-4b3a-8967-ce34ba59df52',
            job_id: '6c215611-0a7d-4b3a-8967-ce34ba59df52',
            project_id: "91443519-836c-4d8b-890c-8ec76ecbcd5c",
            duration: 30,
            state: "ok",
        }],
        job: [
            // for first repo
            {
                id: '2c215611-0a7d-4b3a-8967-ce34ba59df52',
                state: 'finished',
                build_id: "3fc256b0-cc24-47ea-84a9-0816d72fabe6",
                type: 'run_project_container',
                build_only: false,
                dockerfile: 'Dockerfile',
                project_id: "81443519-836c-4d8b-890c-8ec76ecbcd5c",
                name: 'name'
            }, {
                id: '3c215611-0a7d-4b3a-8967-ce34ba59df52',
                state: 'finished',
                build_id: "4fc256b0-cc24-47ea-84a9-0816d72fabe6",
                type: 'run_project_container',
                build_only: false,
                dockerfile: 'Dockerfile',
                project_id: "81443519-836c-4d8b-890c-8ec76ecbcd5c",
                name: 'name'
            },

            // for second repo
            {
                id: '6c215611-0a7d-4b3a-8967-ce34ba59df52',
                state: 'finished',
                build_id: "7fc256b0-cc24-47ea-84a9-0816d72fabe6",
                build_only: false,
                type: 'run_project_container',
                dockerfile: 'Dockerfile',
                project_id: "91443519-836c-4d8b-890c-8ec76ecbcd5c",
                name: 'name second repo'
            }
        ],
        job_stat: [
            {
                job_id: '2c215611-0a7d-4b3a-8967-ce34ba59df52',
                project_id: "81443519-836c-4d8b-890c-8ec76ecbcd5c",
                tests_added: 1,
                tests_duration: 12,
                tests_failed: 1,
                tests_passed: 1,
                tests_skipped: 1,
                tests_error: 1,
            },
            {
                job_id: '3c215611-0a7d-4b3a-8967-ce34ba59df52',
                project_id: "81443519-836c-4d8b-890c-8ec76ecbcd5c",
                tests_added: 1,
                tests_duration: 12,
                tests_failed: 1,
                tests_passed: 1,
                tests_skipped: 1,
                tests_error: 1
            },
            {
                job_id: '6c215611-0a7d-4b3a-8967-ce34ba59df52',
                project_id: "91443519-836c-4d8b-890c-8ec76ecbcd5c",
                tests_added: 1,
                tests_duration: 12,
                tests_failed: 1,
                tests_passed: 1,
                tests_skipped: 1,
                tests_error: 1
            },
        ]
    };

    before(insertData(data));

    let server;
    before(() => {
        server = createServer(false);
    });

    after(() => {
        stopServer(server);
    });

    it('should return 401 if no auth token is set', (done) => {
        request(server)
            .get('/api/dashboard/project/81443519-836c-4d8b-890c-8ec76ecbcd5c/build/3fc256b0-cc24-47ea-84a9-0816d72fabe6/job/2c215611-0a7d-4b3a-8967-ce34ba59df52/stats/history')
            .expect(401, done);
    });

    it('should return 200 and one value', (done) => {
        let token = getToken("ee267114-ec67-4800-853c-ec1325d977fb");
        request(server)
            .get('/api/dashboard/project/81443519-836c-4d8b-890c-8ec76ecbcd5c/job/2c215611-0a7d-4b3a-8967-ce34ba59df52/stats/history')
            .set('auth-token', token)
            .expect(200)
            .expect([{
                build_number: 1,
                job_id: '2c215611-0a7d-4b3a-8967-ce34ba59df52',
                tests_added: 1,
                tests_duration: 12,
                tests_failed: 1,
                tests_passed: 1,
                tests_skipped: 1,
                tests_error: 1
            }], done);
    });

    it('should return 200 and two values', (done) => {
        let token = getToken("ee267114-ec67-4800-853c-ec1325d977fb");
        request(server)
            .get('/api/dashboard/project/81443519-836c-4d8b-890c-8ec76ecbcd5c/job/3c215611-0a7d-4b3a-8967-ce34ba59df52/stats/history')
            .set('auth-token', token)
            .expect(200)
            .expect([{
                build_number: 1,
                job_id: '2c215611-0a7d-4b3a-8967-ce34ba59df52',
                tests_added: 1,
                tests_duration: 12,
                tests_failed: 1,
                tests_passed: 1,
                tests_skipped: 1,
                tests_error: 1
            }, {
                build_number: 2,
                job_id: '3c215611-0a7d-4b3a-8967-ce34ba59df52',
                tests_added: 1,
                tests_duration: 12,
                tests_failed: 1,
                tests_passed: 1,
                tests_skipped: 1,
                tests_error: 1
            }], done);
    });

    it('should return 404 for foreign project', (done) => {
        let token = getToken("ee267114-ec67-4800-853c-ec1325d977fb");
        request(server)
            .get('/api/dashboard/project/91443519-836c-4d8b-890c-8ec76ecbcd5c/job/6c215611-0a7d-4b3a-8967-ce34ba59df52/stats/history')
            .set('auth-token', token)
            .expect(404, done);
    });
});
