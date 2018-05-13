class FakeGPIO():
    def __init__(self):
        self._pins = {}
        self.BCM = None
        self.OUT = None
        return

    def setwarnings(self, bool):
        return

    def setmode(self, mode):
        return

    def setup(self, pin, mode):
        self._pins[pin] = False
        return

    def input(self, pin):
        return self._pins[pin]

    def output(self, pin, state):
        self._pins[pin] = state
        return

class FakeSensor():
    def __init__(self, mode):
        self._temp = 21.12
        self._pressure = 1013.3101
        self._humidity = 50.05
        return

    def read_temperature(self):
        return self._temp

    def read_pressure(self):
        return self._pressure

    def read_humidity(self):
        return self._humidity
