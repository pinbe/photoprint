const names = [
    'photoprint_templates_edit',
    'photo_order',
    'cart_editform',
];

module.exports = {
    targets : names.map(name => {
        return {
            entry: `./src/${name}.ts`,
            output: {
                filename: `${name}.js`
            }
        }
    })
};
