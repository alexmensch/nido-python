module.exports = {
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
				presets: ['react', 'es2015'],
			}
		},
		],
	},
};
