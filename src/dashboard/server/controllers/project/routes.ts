import { Router } from "express";
import { checkProjectAccessPublic, checkProjectAccessPublicName } from "../../utils/auth";
import { db, handleDBError } from "../../db";

const p = Router();

p.get('/name/:project_name/', checkProjectAccessPublicName, (req, res, next) => {
    const project_name = req.params['project_name'];

    db.one(`SELECT p.id, p.name, p.type FROM project p
            WHERE name = $1`, [project_name]).then((pr: any) => {
            res.json(pr);
        }).catch(handleDBError(next));
});

// Private project routes
const project = Router({ mergeParams: true });
project.use('/tokens/', require('./tokens.controller'));
project.use('/collaborators/', require('./collaborators.controller'));
project.use('/secrets/', require('./secret.controller'));
project.use('/build/', require('./build.controller'));
project.use('/job/', require('./job.controller'));
project.use('/', require('./delete.controller'));

p.use('/:project_id/', project);
p.use('/', require('./project.controller'));

const public_project = Router({ mergeParams: true });
// public project routes
public_project.use(checkProjectAccessPublic);
public_project.use('/', require('./public_project.controller'));
public_project.use('/build/', require('./public_build.controller'));
public_project.use('/commit/', require('./public_commit.controller'));
public_project.use('/job/', require('./public_job.controller'));
p.use('/:project_id/', public_project);

module.exports = p;
