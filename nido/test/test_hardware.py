import unittest
from unittest.mock import patch


class TestSensor(unittest.TestCase):
    def test_get_conditions(self):
        p = patch.dict(
            "os.environ",
            {
                "NIDO_BASE": "",
                "NIDOD_MQTT_HOSTNAME": "",
                "NIDOD_MQTT_PORT": "",
                "NIDOD_MQTT_CLIENT_NAME": "",
                "NIDO_TESTING": "",
                "NIDO_TESTING_GPIO": "/tmp/test_gpio.yml",
            },
        )

        p.start()

        from nido.supervisor.hardware import Sensor

        s = Sensor()
        r = s.get_conditions()

        p.stop()

        self.assertEqual(r["conditions"]["temp_c"], 17.17)
        self.assertEqual(r["conditions"]["pressure_mb"], 1013.3101)
        self.assertEqual(r["conditions"]["relative_humidity"], 50.05)


if __name__ == "__main__":
    unittest.main()
