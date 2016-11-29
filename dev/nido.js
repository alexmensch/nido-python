import React from "react";
import ReactDOM from "react-dom";

var Dashboard = React.createClass({
    render: function() {
        return <div>You are logged in and have reached the dashboard.</div>;
    }
});

var LoginForm = React.createClass({
    render: function() {
        return (
            <div className="login">
                <h2>Login</h2>
                <form className="form-horizontal" action="/login" method="post">
                    <div className="form-group">
                        <label for="inputUsername" className="col-sm-2 control-label">Username</label>
                        <div className="col-sm-2">
                            <input type="text" name="username" className="form-control" id="inputUsername" placeholder="Username" />
                        </div>
                    </div>
                    <div className="form-group">
                        <label for="inputPassword" className="col-sm-2 control-label">Password</label>
                        <div className="col-sm-2">
                            <input type="password" name="password" className="form-control" id="inputPassword" placeholder="Password" />
                        </div>
                    </div>
                    <div className="form-group">
                        <div className="col-sm-offset-2 col-sm-2">
                            <button type="submit" className="btn btn-default">Sign in</button>
                        </div>
                    </div> 
                </form>
            </div>
            );
    }
});

var Nido = React.createClass({
        render: function() {
            if (this.props.loginState == false) {
                return <LoginForm />;
            } else {
                return <Dashboard />;
            }
        }
});

// Render and pass Flask login state to Nido component
ReactDOM.render(
  <Nido loginState={(document.getElementById('nido').getAttribute('loginState') == 'true') ? true : false} />,
  document.getElementById('nido')
);
