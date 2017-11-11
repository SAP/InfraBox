'use strict'
const merge = require('webpack-merge')
const prodEnv = require('./prod.env')

module.exports = merge(prodEnv, {
  NODE_ENV: '"development"',
  DASHBOARD_HOST: '"localhost"',
  API_PATH: '"http://localhost/api/dashboard/"',
})
