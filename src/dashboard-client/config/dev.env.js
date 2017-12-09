'use strict'
const merge = require('webpack-merge')
const prodEnv = require('./prod.env')

module.exports = merge(prodEnv, {
  NODE_ENV: '"development"',
  DASHBOARD_HOST: '"localhost:8090"',
  API_PATH: '"http://localhost:8090/api/dashboard/"',
  NEW_API_PATH: '"http://localhost:8090/api/v1/"'
})
