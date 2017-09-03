"use strict";
const express_1 = require("express");
const p = express_1.Router();
p.use('/github/hook/', require('./hook.controller'));
p.use('/project/', require('./project.controller'));
p.use('/project/', require('./upload.controller'));
module.exports = p;
