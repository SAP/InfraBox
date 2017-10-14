import { Router } from "express";
import { auth, checkProjectAccess, checkProjectAccessPublic } from "../../utils/auth";

const p = Router();

const public_project = Router({ mergeParams: true });
// public project routes
public_project.use(checkProjectAccessPublic);
public_project.use('/', require('./public_project.controller'));
public_project.use('/build/', require('./public_build.controller'));
public_project.use('/commit/', require('./public_commit.controller'));
public_project.use('/job/', require('./public_job.controller'));
p.use('/:project_id/', public_project);

// Private project routes
const project = Router({ mergeParams: true });
project.use(auth);
project.use(checkProjectAccess);
project.use('/tokens/', require('./tokens.controller'));
project.use('/collaborators/', require('./collaborators.controller'));
project.use('/secrets/', require('./secret.controller'));
project.use('/build/', require('./build.controller'));
project.use('/job/', require('./job.controller'));
project.use('/', require('./delete.controller'));

p.use('/:project_id/', project);
p.use('/', auth, require('./project.controller'));

module.exports = p;
