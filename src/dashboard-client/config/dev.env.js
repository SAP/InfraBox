'use strict'
const merge = require('webpack-merge')
const prodEnv = require('./prod.env')

module.exports = merge(prodEnv, {
  NODE_ENV: '"development"',
  DASHBOARD_HOST: '"infrabox.ninja"',
  API_PATH: '"https://infrabox.ninja/api/dashboard/"',
})
