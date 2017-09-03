import { Router } from "express";

const p = Router();
p.use('/github/hook/', require('./hook.controller'));
p.use('/project/', require('./project.controller'));
p.use('/project/', require('./upload.controller'));

module.exports = p;
