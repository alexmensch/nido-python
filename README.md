# Prerequisites
- You will need `python3` installed as the installation environment is built within `venv`. The core application code is also compatible with Python 2.7 using `futurize`, but you will need to build your own environment.
```
sudo apt-get install python3 python3-venv python3-pip
```
- To build the frontend application, you will need Node.js installed. (The steps below are from the [Node.js website](https://nodejs.org/en/download/package-manager/#debian-and-ubuntu-based-linux-distributions).)
```
curl -sL https://deb.nodesource.com/setup_10.x | sudo -E bash -
sudo apt-get install -y nodejs
```

# Installation
Run `source ./install` to install required Python modules and Node.js components.

## Initial application configuration
1. Rename `nido/cfg/config-example.yaml` to `nido/cfg/config.yaml` with your own settings.
2. Rename `private-config.py.example` to `instance/private-config.py` with your own settings.

# Running the application
1. `run-nido.sh -b <base path> [-d]` This runs either Flask/Werkzeug (when the `-d` debug flag is set) or gunicorn. The hardware controller/scheduler daemon is also started.
> Note: `sudo` access is required due to hardware access to GPIO pins
2. (Optional) You may want to add this line to your `/etc/rc.local` file so that Nido runs automatically at startup. Output from the server will be output to `nohup.out` in your base path.
```
su <pi user> && cd <base path> && nohup ./run-nido.sh -b <base path> &
```

# Stopping the application
1. `stop-nido.sh -b <base path> [-t]` See below for information on the `-t` option.

# Testing and Development

## Generating a test build of the frontend JS
`npm run build`

#### Optional (automate jsx -> js translation)
1. Install watchman as per instructions [here](https://facebook.github.io/watchman/docs/install.html)
2. Watch the React source: `watchman watch ./app`
3. Run build process on file changes: `watchman -- trigger ./app build-jsx '*.js' -- npm run build`

## Testing on a non-Raspberry Pi platform
To bypass the hardware libraries, you can run `run-nido.sh` with the `-t` flag. The `Testing.py` library will return static sensor information instead and store GPIO pin status in a disk on file.
