/* tslint:disable */

// polyfills
import 'core-js';

// (these modules are what is in 'angular2/bundles/angular2-polyfills' so don't use that here)
import 'reflect-metadata';

require('zone.js/dist/zone');

window['jQuery'] = window['$'] = require('jquery/dist/jquery.min');
require('bootstrap-loader');
require('font-awesome/css/font-awesome.css');
require('metismenu/dist/metisMenu');
require('imports?Raphael=webpack-raphael!morris.js/morris.min.js');
require('toastr');
require('toastr/build/toastr.css');
require('raphael/raphael.min.js');
require('taucharts/build/production/tauCharts.min.js');
require('taucharts/build/production/tauCharts.default.min.css');
require('octicons/build/octicons.css')
require('octicons/build/sprite.octicons.svg')
/* tslint:enable */
