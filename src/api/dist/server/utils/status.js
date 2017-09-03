"use strict";
function NotFound() {
    this.name = "NotFound";
    this.message = "Not Found";
    this.status = 404;
    this.infrabox_error = true;
    this.ignore_error = true;
}
exports.NotFound = NotFound;
NotFound.prototype = Error.prototype;
function BadRequest(message) {
    this.name = "BadRequest";
    this.message = (message || "Bad Request");
    this.status = 400;
    this.infrabox_error = true;
    this.ignore_error = true;
}
exports.BadRequest = BadRequest;
BadRequest.prototype = Error.prototype;
function Unauthorized() {
    this.name = "Unauthorized";
    this.message = "Unauthorized";
    this.status = 401;
    this.infrabox_error = true;
    this.ignore_error = true;
}
exports.Unauthorized = Unauthorized;
Unauthorized.prototype = Error.prototype;
function OK(res, message, data = null) {
    res.status(200);
    const m = { message: message, type: "success" };
    if (data) {
        m['data'] = data;
    }
    res.json(m);
}
exports.OK = OK;
function InternalError(err) {
    this.name = "InternalError";
    this.message = "Internal Server Error";
    this.details = err;
    this.status = 500;
    this.infrabox_error = true;
    this.ignore_error = false;
}
exports.InternalError = InternalError;
InternalError.prototype = Error.prototype;
function CreateFinalHandler(res, next, message) {
    return (err) => {
        if (err) {
            if (err.infrabox_error) {
                // just forward it
                return next(err);
            }
            else {
                // some other error, wrap it in out error
                return next(new InternalError(err));
            }
        }
        return OK(res, message);
    };
}
exports.CreateFinalHandler = CreateFinalHandler;
