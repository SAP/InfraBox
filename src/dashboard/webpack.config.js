const webpack = require('webpack');
const path = require('path');

const CopyWebpackPlugin = require('copy-webpack-plugin');

const config = {
    entry: {
        'vendor': './client/vendor',
        'app': './client/main',
        'index': './client/index'
    },
    output: {
        path: path.resolve(__dirname, './dist/client'),
        filename: '[name].js'
    },
    resolve: {
        extensions: ['.ts', '.es6', '.js', '.json']
    },
    module: {
        loaders: [
            // Bootstrap 3
            { test:/bootstrap-sass[\/\\]assets[\/\\]javascripts[\/\\]/, loader: 'imports?jQuery=jquery' }
        ],
        rules: [
            { enforce: 'pre', test: /\.ts$/, exclude: /node_modules/, loader: 'tslint' },
            {
                test: /\.ts$/,
                exclude: /node_modules/,
                loaders: ['awesome-typescript-loader', 'angular2-template-loader']
            }, {
                test: /\.json$/,
                loader: 'json'
            }, {
                test: /\.html/,
                loader: 'html?minimize=false'
            }, {
                test: /\.styl$/,
                loader: 'css!stylus'
            }, {
                test: /\.css$/,
                loader: 'style!css'
            }, {
                test: /\.(svg|mp4|gif|png|jpe?g)$/i,
                loader: 'file?name=dist/images/[name].[ext]'
            }, {
                test: /\.woff2?$/,
                loader: 'url?name=dist/fonts/[name].[ext]&limit=10000&mimetype=application/font-woff'
            }, {
                test: /\.(ttf|eot|svg)$/,
                loader: 'file?name=dist/fonts/[name].[ext]'
            }
        ]
    }
};

function root(__path) {
  return path.join(__dirname, __path);
}

if (!(process.env.WEBPACK_ENV === 'production')) {
    config.devtool = 'source-map';
    config.plugins = [
        new webpack.DefinePlugin({
            'WEBPACK_ENV': '"dev"'
        }),
        new webpack.ContextReplacementPlugin(
            // The (\\|\/) piece accounts for path separators in *nix and Windows
            /angular(\\|\/)core(\\|\/)(esm(\\|\/)src|src)(\\|\/)linker/,
            root('./client')
        )
    ]
} else {
    config.plugins = [
        new webpack.optimize.UglifyJsPlugin({
            compress: {
                screw_ie8: true,
                warnings: false
            },
            comments: false
        }),
        new webpack.DefinePlugin({
            'WEBPACK_ENV': '"production"'
        }),
        new CopyWebpackPlugin([{
            from: './src/index.html'
        }], {})
    ];
}

module.exports = config;
