var gulp = require("gulp");
var nodemon = require("gulp-nodemon");
var plumber = require("gulp-plumber");
var ts = require("gulp-typescript");
var rimraf = require("gulp-rimraf");
var livereload = require("gulp-livereload");
var _ = require("lodash");
var tslint = require("gulp-tslint");
var typescriptFormatter = require("gulp-typescript-formatter");

gulp.task("format", function () {
    return gulp.src("src/**/*.ts")
        .pipe(typescriptFormatter({
            baseDir: ".",
            tslint: true,
            editorconfig: true
        }))
        .pipe(gulp.dest('./src'));
});

var deleted = false;
gulp.task("empty-dist", function() {
    if (deleted) {
        return;
    }

    deleted = true;
    return gulp.src("dist/server", {
            read: false
        })
        .pipe(rimraf());
});

var tsProject = ts.createProject("tsconfig.json");
gulp.task("compile", ["empty-dist"], function() {
    return gulp.src("server/**/*.ts")
        .pipe(tsProject())
        .pipe(gulp.dest("dist/server"));
});

gulp.task("develop", ["build-server"], function() {
    livereload.listen();
    nodemon({
        script: "dist/server/app.js",
        ext: "js html css",
        stdout: false,
        watch: ["dist"]
    }).on("readable", function() {
        this.stdout.on("data", function(chunk) {
            if (/^Express server listening on port/.test(chunk)) {
                livereload.changed(__dirname);
            }
        });
        this.stdout.pipe(process.stdout);
        this.stderr.pipe(process.stderr);
    });
});

gulp.task("server-copy-views", ["empty-dist"], function() {
    return gulp.src(["server/views/**"]).pipe(gulp.dest("dist/server/views"));
});

gulp.task("server-copy-public", ["empty-dist"], function() {
    return gulp.src(["server/public/**"]).pipe(gulp.dest("dist/server/public"));
});

gulp.task("server-copy-config-schema", ["empty-dist"], function() {
    return gulp.src(["config/**"]).pipe(gulp.dest("dist/server/config"));
});

gulp.task("tslint", function() {
    return gulp.src("**/*.ts")
        .pipe(tslint({
            formatter: "verbose"
        }))
        .pipe(tslint.report());
});

gulp.task("build-server", ["server-copy-views", "server-copy-public", "server-copy-config-schema", "compile"]);

gulp.task("watch-ts", ["build-server"], function() {
    gulp.watch("server/**/*.ts", ["compile"]);
});

gulp.task("default", [
    "develop", "watch-ts"
]);

gulp.task("production", [
    "develop"
]);
