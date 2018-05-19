# Prerequisites
- The application code is compatible with both Python 2.7 and Python 3. You will need `pip` or `pip3` installed as appropriate.
- For the frontend application, you will need Node.js installed. Instructions can be found on the [Node.js website](https://nodejs.org/en/download/package-manager/#debian-and-ubuntu-based-linux-distributions).

# Installation
Run `install.sh [-2]` to install required Python modules and Node.js components. The `-2` flag should be used for a Python 2.7 installation.

## Initial application configuration
1. Rename `app/cfg/config-example.yaml` to `app/cfg/config.yaml` with your own settings.

## Generating a production build of the frontend JavaScript
`npm run build-prod`

# Running the application
1. `run-nido.sh -b <base path> [-2]` This runs both the Flask HTTP server and the controller/scheduler daemon. If you need to run the application on Python 2.7, you need to add the `-2` flag.
> Note: `sudo` access is required due to hardware access to GPIO pins
2. (Optional) You may want to add this line to your `/etc/rc.local` file so that Nido runs automatically at startup. Output from the Flask server will be output to `nohup.out` in your base path.
```
su <pi user> && cd <base path> && nohup ./run-nido.sh -b <base path> [-2] &
```

# Testing and Development

## Generating a test build of the frontend JS
`npm run build`

#### Optional (automate jsx -> js translation)
1. Install watchman as per instructions [here](https://facebook.github.io/watchman/docs/install.html)
2. Watch the React source: `watchman watch ./app`
3. Run build process on file changes: `watchman -- trigger ./app build-jsx '*.js' -- npm run build`

## Debugging the backend application
You can run `run-nido.sh` with the `-d` for additional debug output in the logs.

## Testing on a non-Raspberry Pi platform
To bypass the hardware libraries, you can run `run-nido.sh` with the `-t` flag. The `Testing.py` library will return static sensor information instead and store GPIO pin status in a disk on file.
