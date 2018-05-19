import yaml


class FakeGPIO():
    def __init__(self, state_file):
        self._pins = {}
        self.BCM = None
        self.OUT = None
        self._state = state_file
        self._write()
        return None

    def setwarnings(self, bool):
        return None

    def setmode(self, mode):
        return None

    def setup(self, pin, mode):
        self._get_pins()
        if pin not in self._pins:
            self._set_pin(pin, False)
        return None

    def input(self, pin):
        self._get_pins()
        return self._pins[pin]

    def output(self, pin, state):
        self._set_pin(pin, state)
        return None

    def _set_pin(self, pin, state):
        self._pins[pin] = state
        self._write()
        return None

    def _get_pins(self):
        with open(self._state, 'r') as f:
            self._pins = yaml.load(f)
        return None

    def _write(self):
        with open(self._state, 'w') as f:
            yaml.dump(self._pins, f, default_flow_style=False, indent=4)
        return None


class FakeSensor():
    def __init__(self, mode):
        self._temp = 17.17
        self._pressure = 101331.01
        self._humidity = 50.05
        return None

    def read_temperature(self):
        return self._temp

    def read_pressure(self):
        return self._pressure

    def read_humidity(self):
        return self._humidity
