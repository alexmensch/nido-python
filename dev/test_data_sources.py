from lib.CollectData import Sensor, LocalWeather

sensor = Sensor()
weather = LocalWeather(94115)

print repr(sensor.conditions)
print repr(weather.conditions)
