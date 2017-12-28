#!/bin/bash -e

infrabox_host=${1:-"http://localhost:8080/api"}

_runSingleTest() {
    pushd "$1"
    echo "## Run test: $1"
    export INFRABOX_API_URL=$infrabox_host
    infrabox push --show-console
    popd
}

_runDockerJobTests() {
    _runSingleTest "docker_job"
    _runSingleTest "docker_secure_env"
    _runSingleTest "docker_insecure_env"
    _runSingleTest "docker_input_output"
    _runSingleTest "resources_kubernetes"

    echo "## TODO: docker: testresult"
    echo "## TODO: docker: badge"
    echo "## TODO: docker: markup"
    echo "## TODO: docker: caching"
}

_runDockerComposeJobTests() {
    _runSingleTest "docker_compose_job"

    echo "## TODO: compose: caching"
    echo "## TODO: compose: insecure environment vars"
    echo "## TODO: compose: secure environment vars"
    echo "## TODO: compose: output/input"
    echo "## TODO: compose: testresult"
    echo "## TODO: compose: badge"
    echo "## TODO: compose: markup"
}

_runTests() {
    _runDockerJobTests
    _runDockerComposeJobTests
}

_runTests
