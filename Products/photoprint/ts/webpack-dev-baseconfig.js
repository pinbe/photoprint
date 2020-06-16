const commonConfig = require('./webpack-common-baseconfig').baseConfig;
let baseConfig = {
    devtool: "source-map",
    watch: true,
    watchOptions: {
        poll: 500,
        ignored: /node_modules/,
    },
    mode: 'development'
};

module.exports = {baseConfig: Object.assign({}, commonConfig, baseConfig)};