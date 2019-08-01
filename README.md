*This respository is the primary library that the Nido smart thermostat is built around. If you're looking for instructions on how to run Nido on a Raspberry Pi, see <https://github.com/alexmensch/nido> for instructions and the full project background.*

## Quickstart
```bash
npm install nido
```

## Running the application locally for development
### Requirements and initial configuration
1. Nido has been tested with Python 3.6.5 and higher. Python 2 is not supported.
2. You will need both [Docker and Docker Compose](https://www.docker.com/get-started) installed locally.
3. Rename `private-config.py.example` to `private-config.py` with your own private settings.

### Starting the Nido backend and API server
`> docker-compose up`

Run Docker Compose from the base of the project to run the Nido thermostat and API locally. If you are not running on a Raspberry Pi, a test hardware fixture will be loaded instead of the native Raspberry Pi GPIO library.

**Docker local volume mappings**

- `nido/` Local changes to the package source code are mapped to the Docker containers.
- `instance/` Nido settings and scheduler database entries are stored outside the container.
- `log/` Logs generated by backend RPC service and scheduler are generated here.

### Shutting down Nido
`> docker-compose down`

### Scripts and development tools

- `clean.sh` Delete all local and cached files generated by running in your local environment.
- `build.sh` Build the Nido package for distribution.
- `pip install -r dev_requirements.txt` Installs packages useful for local development. Using Python `venv` is recommended.
