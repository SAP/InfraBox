"use strict";
const express_1 = require("express");
const db_1 = require("../db");
const status_1 = require("../utils/status");
const gcs_1 = require("../utils/gcs");
const logger_1 = require("../utils/logger");
const fs = require('fs');
const uuid = require('uuid');
const multer = require('multer');
const storage = multer.diskStorage({
    destination: '/tmp/infrabox/project_upload/',
    limits: { fileSize: 1024 * 1024 * 100 }
});
const upload = multer({ storage: storage });
const router = express_1.Router();
module.exports = router;
router.post("/:project_id/upload", upload.single('project.zip'), (req, res, next) => {
    // TODO(Steffen): check permission
    // TODO(Steffen): validate input
    const file = req["file"].path;
    const project_id = req.params['project_id'];
    if (!req.headers['authorization']) {
        fs.unlinkSync(file);
        logger_1.logger.debug('no authorization header set');
        return next(new status_1.Unauthorized());
    }
    const data = {
        build: {
            id: uuid.v4(),
            number: 1
        }
    };
    db_1.db.tx((tx) => {
        return tx.any(`
            SELECT u.id as user_id
            FROM auth_token at
            INNER JOIN "user" u
                ON u.id = at.user_id
                AND at.token = $1
            INNER JOIN collaborator co
                ON co.user_id = u.id
            INNER JOIN project p
                ON p.id = co.project_id
                AND p.id = $2
                AND p.type = 'upload'
        `, [req.headers['authorization'], project_id])
            .then((result) => {
            if (result.length !== 1) {
                logger_1.logger.debug('project not found for id and token');
                throw new status_1.Unauthorized();
            }
            const destination = data.build.id + ".zip";
            return gcs_1.uploadProject(file, destination);
        }).then(() => {
            return db_1.db.one(`
                SELECT count(distinct build_number) + 1 AS build_number
                FROM build AS b
                WHERE b.project_id = $1
            `, [project_id]);
        })
            .then((b) => {
            data.build.number = b.build_number;
            return db_1.db.one(`
                INSERT INTO source_upload(filename, project_id, filesize) VALUES ($1, $2, $3) RETURNING ID
            `, [data.build.id + '.zip', project_id, 123]);
        })
            .then((b) => {
            return db_1.db.none(`
                INSERT INTO build (commit_id, build_number, project_id, source_upload_id, id) VALUES ($1, $2, $3, $4, $5)
            `, [null, data.build.number, project_id, b.id, data.build.id]);
        })
            .then(() => {
            return db_1.db.none(`
                INSERT INTO job (id, state, build_id, type, name, project_id, dockerfile, build_only, cpu, memory)
                    VALUES (gen_random_uuid(), 'queued', $1, 'create_job_matrix', 'Create Jobs', $2, '', false, 1, 1024);
            `, [data.build.id, project_id]);
        });
    })
        .then(() => {
        fs.unlinkSync(file);
        return status_1.OK(res, 'successfully started build', data);
    }).catch((err) => {
        fs.unlinkSync(file);
        db_1.handleDBError(next)(err);
    });
});
