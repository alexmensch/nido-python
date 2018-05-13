## Prerequisites
You will need Node.js installed, instructions can be found on the [Node.js website](https://nodejs.org/en/download/package-manager/#debian-and-ubuntu-based-linux-distributions).

## Installation
Run `install.sh` to install required Python modules and Node.js components.

## Initial configuration
1. Rename `app/cfg/config-example.yaml` to `app/cfg/config.yaml` with your own settings.
2. Set absolute path to `config.yaml` in `app/lib/Nido.py`.

## Generating a test build
`npm run build`

#### Optional (automate jsx -> js translation)
1. Install watchman as per instructions [here](https://facebook.github.io/watchman/docs/install.html)
2. Watch the React source: `watchman watch ./app`
3. Run build process on file changes: `watchman -- trigger ./app build-jsx '*.js' -- npm run build`

## Generating a production build
`npm run build-prod`

## Running the application
1. `run-nido.sh -b <base path>` (Runs both Flask HTTP server and daemon)
> Note: `sudo` is required due to hardware access to GPIO pins
2. (Optional) You may want to add this line to your `/etc/rc.local` file so that Nido runs automatically at startup. Output from the Flask server will be output to `nohup.out` in your base path.
```
su <pi user> && cd <base path> && nohup ./run-nido.sh -b <base path> &
```
