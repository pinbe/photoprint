const path = require('path');
const baseConfig = require('./webpack-prod-baseconfig').baseConfig;
const targets = require('./webpack-targets').targets;



module.exports = env => {
    let targets_ = [];

    for (let i in targets) {
        let target = targets[i];
        target.output.path = path.resolve(__dirname, '../skins/photoprint/jsbuild');
        target.output.publicPath = '/photoprint/jsbuild/';
        targets_.push(Object.assign({}, baseConfig, target));
    }
    if (env && env.target) {
        targets_ = targets_.filter(t => t.entry === env.target);
    }
    return targets_;
};
