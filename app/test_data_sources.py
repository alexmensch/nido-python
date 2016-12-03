from lib.CollectData import Sensor, LocalWeather

s = Sensor()
w = LocalWeather()

print repr(s.get_conditions())
print repr(w.get_conditions())
