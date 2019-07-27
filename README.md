# Why build yet another smart thermostat?

> Introduction to use case and background

# Running the application on a Raspberry Pi
## The easy way
Refer to <https://github.com/alexmensch/nido-deploy> for instructions.

## The hard(er) way
> List of manual steps

# Running the application locally for development
## Initial configuration
1. Rename `config/private-config.py.example` to `config/private-config.py` with your own private settings.
2. You will need [Docker and Docker Compose](https://www.docker.com/get-started) installed locally.

## Running the application
Run `docker-compose up` from the base of the project to start all components locally. If you are not running on a Raspberry Pi, a test hardware fixture will be loaded instead of the native GPIO library.

## Stopping the application
Run `docker-compose down`.
