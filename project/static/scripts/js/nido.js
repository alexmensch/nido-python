(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);throw new Error("Cannot find module '"+o+"'")}var f=n[o]={exports:{}};t[o][0].call(f.exports,function(e){var n=t[o][1][e];return s(n?n:e)},f,f.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
/** @jsx React.DOM */

var ConfigOptions = React.createClass({displayName: "ConfigOptions",
	render: function() {
		return (
			React.createElement("div", {className: "ConfigOptions"}, 
			React.createElement("h1", null, "Configuration"), 
			React.createElement(ConfigList, null)
			)
		       );
	}
});

var ConfigList = React.createClass({displayName: "ConfigList",
	render: function() {
		return (
			React.createElement("div", {className: "ConfigList"}, 
			React.createElement(ConfigText, {setting: "Nido location name"}, "Living Room"), 
			React.createElement(ConfigText, {setting: "Zipcode"}, "94115"), 
			React.createElement(ConfigChoice, {setting: "Temperature scale", values: ""})
			)
		       );
	}
});


var ConfigText = React.createClass({displayName: "ConfigText",
	render: function() {
		return (
			React.createElement("div", {className: "ConfigText"}, 
			this.props.setting, ": ", React.createElement("input", {
				type: "text", 
				value: this.props.children}
			)
			)
		       );
	}
});

var ConfigChoice = React.createClass({displayName: "ConfigChoice",
	render: function() {
		return (
			React.createElement("div", {className: "ConfigChoice"}, 
			this.props.setting, ": ", React.createElement("select", null, 
			"// TODO: Generate option tags"
			)
			)
			);
		}
});

React.render(
	React.createElement(ConfigOptions, null),
	document.getElementById('content')
);


},{}]},{},[1])