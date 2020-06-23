module.exports = {
    defaultNamespace: 'photoprint',
    locales: ['en', 'fr'],
    input: 'src/**/*.ts',
    output: '../skins/photoprint/jsbuild/locales/$LOCALE/$NAMESPACE.json',
    useKeysAsDefaultValue: true,
    verbose: true,

    lexers:{
        ts: [{
            lexer: 'JavascriptLexer',
            functions: ['_'],
        }]
    },
};