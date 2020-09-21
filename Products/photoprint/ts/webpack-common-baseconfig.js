let baseConfig = {
    module: {
        rules: [
            {test: /\.tsx?$/, loader: "awesome-typescript-loader"},
            {enforce: "pre", test: /\.js$/, loader: "source-map-loader"},
            {
                test: /\.css$/,
                use: [
                    'style-loader',
                    'css-loader']
            },
            {
                test: /\.(scss)$/,
                use: [{
                    loader: 'style-loader', // inject CSS to page
                }, {
                    loader: 'css-loader', // translates CSS into CommonJS modules
                }, {
                    loader: 'postcss-loader', // Run postcss actions
                    // options: {
                    //     plugins: function() { // postcss plugins, can be exported to postcss.config.js
                    //         return [
                    //             require('autoprefixer')
                    //         ];
                    //     }
                    // }
                }, {
                    loader: 'sass-loader' // compiles Sass to CSS
                }]
            },            // {
            //     test: /\.s[ac]ss$/i,
            //     use: [
            //         // Creates `style` nodes from JS strings
            //         'style-loader',
            //         // Translates CSS into CommonJS
            //         'css-loader',
            //         // Compiles Sass to CSS
            //         'sass-loader',
            //     ],
            // },
            {
                test: /\.woff(2)?(\?v=[0-9]\.[0-9]\.[0-9])?$/,
                use: {
                    loader: 'url-loader',
                    options: {
                        name: '[path][name].[ext]'
                    }
                }
            },
            {
                test: /\.(ttf|eot|svg)(\?v=[0-9]\.[0-9]\.[0-9])?$/,
                use: "file-loader"
            }
        ]
    },
    resolve: {
        extensions: ['.tsx', '.ts', '.js']
    },
};
module.exports = {baseConfig: baseConfig};