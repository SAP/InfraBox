import { Router, Request, Response } from "express";
import { db, handleDBError } from "../db";
import { OK, Unauthorized } from "../utils/status";
import { uploadProject } from "../utils/gcs";
import { logger } from "../utils/logger";
import fs = require('fs');
import uuid = require('uuid');

const multer = require('multer');

const storage = multer.diskStorage({
  destination: '/tmp/infrabox/project_upload/',
  limits: { fileSize: 1024 * 1024 * 100 }
});

const upload = multer({ storage: storage });
const router = Router();

module.exports = router;

router.post("/:project_id/upload", upload.single('project.zip'), (req: Request, res: Response, next) => {
    // TODO(Steffen): check permission
    // TODO(Steffen): validate input

    const file = req["file"].path;
    const project_id = req.params['project_id'];

    if (!req.headers['authorization']) {
        fs.unlinkSync(file);
        logger.debug('no authorization header set');
        return next(new Unauthorized());
    }

    const data = {
        build: {
            id: uuid.v4(),
            number: 1
        }
    };

    db.tx((tx) => {
        return tx.any(`
            SELECT token
            FROM auth_token at
            INNER JOIN project p
                ON  at.project_id = p.id
                AND at.token = $1
                AND p.id = $2
                AND p.type = 'upload'
        `, [req.headers['authorization'], project_id])
        .then((result: any[]) => {
            if (result.length !== 1) {
                logger.debug('project not found for id and token');
                throw new Unauthorized();
            }

            const destination = data.build.id + ".zip";
            return uploadProject(file, destination);
        }).then(() => {
            return db.one(`
                SELECT count(distinct build_number) + 1 AS build_number
                FROM build AS b
                WHERE b.project_id = $1
            `, [project_id]);
        })
        .then((b: any) => {
            data.build.number = b.build_number;
            return db.one(`
                INSERT INTO source_upload(filename, project_id, filesize) VALUES ($1, $2, $3) RETURNING ID
            `, [data.build.id + '.zip', project_id, 123]);
        })
        .then((b: any) => {
            return db.none(`
                INSERT INTO build (commit_id, build_number, project_id, source_upload_id, id) VALUES ($1, $2, $3, $4, $5)
            `, [null, data.build.number, project_id, b.id, data.build.id]);
        })
        .then(() => {
            return db.none(`
                INSERT INTO job (id, state, build_id, type, name, project_id, dockerfile, build_only, cpu, memory)
                    VALUES (gen_random_uuid(), 'queued', $1, 'create_job_matrix', 'Create Jobs', $2, '', false, 1, 1024);
            `, [data.build.id, project_id]);
        });
    })
    .then(() => {
        fs.unlinkSync(file);
        return OK(res, 'successfully started build', data);
    }).catch((err) => {
        fs.unlinkSync(file);
        handleDBError(next)(err);
    });
});
