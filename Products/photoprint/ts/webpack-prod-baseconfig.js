const commonConfig = require('./webpack-common-baseconfig').baseConfig;
const WebpackObfuscator = require('webpack-obfuscator');

const baseConfig = {
    watch: false,
    mode: 'production',
    // plugins: [
    //     new WebpackObfuscator({rotateStringArray: true})
    // ]
};

module.exports = {baseConfig: Object.assign({}, commonConfig, baseConfig)};