import yaml


class FakeGPIO():
    def __init__(self, state_file):
        self._pins = {}
        self.BCM = None
        self.OUT = None
        self._state = state_file
        self._write()
        return

    def setwarnings(self, bool):
        return

    def setmode(self, mode):
        return

    def setup(self, pin, mode):
        self._get_pins()
        if pin not in self._pins:
            self._set_pin(pin, False)
        return

    def input(self, pin):
        self._get_pins()
        return self._pins[pin]

    def output(self, pin, state):
        self._set_pin(pin, state)
        return

    def _set_pin(self, pin, state):
        self._pins[pin] = state
        self._write()
        return

    def _get_pins(self):
        with open(self._state, 'r') as f:
            self._pins = yaml.load(f)
        return

    def _write(self):
        with open(self._state, 'w') as f:
            yaml.dump(self._pins, f, default_flow_style=False, indent=4)


class FakeSensor():
    def __init__(self, mode):
        self._temp = 21.12
        self._pressure = 101331.01
        self._humidity = 50.05
        return

    def read_temperature(self):
        return self._temp

    def read_pressure(self):
        return self._pressure

    def read_humidity(self):
        return self._humidity
