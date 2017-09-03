"use strict";
const _ = require("lodash");
let pattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-4][0-9a-f]{3}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
function isUUID(value) {
    if (!_.isString(value)) {
        return false;
    }
    let b = pattern.test(value);
    return b;
}
exports.isUUID = isUUID;
