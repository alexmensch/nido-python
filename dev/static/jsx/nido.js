/** @jsx React.DOM */

var ConfigOptions = React.createClass({
	render: function() {
		return (
			<div className="ConfigOptions">
			<h1>Configuration</h1>
			<ConfigList />
			</div>
		       );
	}
});

var ConfigList = React.createClass({
	render: function() {
		return (
			<div className="ConfigList">
			<ConfigText setting="Nido location name">Living Room</ConfigText>
			<ConfigText setting="Zipcode">94115</ConfigText>
			<ConfigChoice setting="Temperature scale" values="" />
			</div>
		       );
	}
});


var ConfigText = React.createClass({
	render: function() {
		return (
			<div className="ConfigText">
			{this.props.setting}: <input
				type="text"
				value={this.props.children}
			/>
			</div>
		       );
	}
});

var ConfigChoice = React.createClass({
	render: function() {
		return (
			<div className="ConfigChoice">
			{this.props.setting}: <select>
			// TODO: Generate option tags
			</select>
			</div>
			);
		}
});

React.render(
	React.createElement(ConfigOptions, null),
	document.getElementById('content')
);
