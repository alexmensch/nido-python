module.exports = {
	context: __dirname + "/app",
	entry: {
		javascript: './nido.js',
	},

	output: {
		filename: "nido.js",
		path: __dirname + "/app/static/js",
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
}
