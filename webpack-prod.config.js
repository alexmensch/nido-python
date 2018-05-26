const webpack = require('webpack');

module.exports = {
        devtool: 'cheap-module-source-map',
	context: __dirname + "/nido",
	entry: {
		javascript: '../react/nido.js',
	},

	output: {
		filename: "nido.js",
		path: __dirname + "/nido/static/js",
	},

	module: {
		loaders: [
		{
			test: /\.js$/,
			exclude: /node_modules/,
			loader: "babel-loader",
			query: {
				presets: ['react', 'env'],
			}
		},
		],
	},
        plugins: [
            new webpack.DefinePlugin({
                'process.env': {
                    'NODE_ENV': JSON.stringify('production')
                }
            })
        ],
};
