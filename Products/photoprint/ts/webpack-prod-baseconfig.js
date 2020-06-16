const commonConfig = require('./webpack-common-baseconfig').baseConfig;
const TerserPlugin = require('terser-webpack-plugin');
const baseConfig = {
    watch: false,
    mode: 'production',
    optimization: {
        minimize: true,
        minimizer: [new TerserPlugin({
            terserOptions: {
                mangle: true
            }
        })]
    }
};

module.exports = {baseConfig: Object.assign({}, commonConfig, baseConfig)};