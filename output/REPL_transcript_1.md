```python
from machine import Pin

import onewire

import ds18x20

import time



bus = onewire.OneWire(Pin(4))

sensor = ds18x20.DS18X20(bus)



roms = sensor.scan()

print("Sensors found:", len(roms))

print("ROM addresses:", \[r.hex() for r in roms])



if roms:

&#x20;   sensor.convert\_temp()

&#x20;   time.sleep\_ms(750)



&#x20;   for rom in roms:

&#x20;       temp\_c = sensor.read\_temp(rom)

&#x20;       print("Temperature:", temp\_c, "C")
```


```python

sensor.convert\_temp()

time.sleep\_ms(750)

print("Temp:", sensor.read\_temp(roms\[0]), "C")

```




```text

>>> print("Temp: ", sensor.read\_temp(roms\[0]), "C")

Temp:  17.25 C

>>> sensor.convert\_temp()

>>> time.sleep\_ms(750)

>>> print("Temp:", sensor.read\_temp(roms\[0]), "C")

Temp: 20.0 C

>>> sensor.convert\_temp()

>>> time.sleep\_ms(750)

>>> print("Temp:", sensor.read\_temp(roms\[0]), "C")

Temp: 23.5 C

>>> sensor.convert\_temp()

>>> time.sleep\_ms(750)

>>> print("Temp:", sensor.read\_temp(roms\[0]), "C")

Temp: 23.25 C

>>> sensor.convert\_temp()

>>> time.sleep\_ms(750)

>>> print("Temp:", sensor.read\_temp(roms\[0]), "C")

Temp: 23.0625 C

>>> sensor.convert\_temp()

>>> time.sleep\_ms(750)

>>> print("Temp:", sensor.read\_temp(roms\[0]), "C")

Temp: 22.75 C

>>> >>> print("Temp: ", sensor.read\_temp(roms\[0]), "C")

Traceback (most recent call last):

&#x20; File "<stdin>", line 1

SyntaxError: invalid syntax

>>> Temp:  17.25 C

Traceback (most recent call last):

&#x20; File "<stdin>", line 1

SyntaxError: invalid syntax

>>> >>> sensor.convert\_temp()

Traceback (most recent call last):

&#x20; File "<stdin>", line 1

SyntaxError: invalid syntax

>>> >>> time.sleep\_ms(750)

Traceback (most recent call last):

&#x20; File "<stdin>", line 1

SyntaxError: invalid syntax

>>> >>> print("Temp:", sensor.read\_temp(roms\[0]), "C")

Traceback (most recent call last):

&#x20; File "<stdin>", line 1

SyntaxError: invalid syntax

>>> Temp: 20.0 C

Traceback (most recent call last):

&#x20; File "<stdin>", line 1

SyntaxError: invalid syntax

>>> >>> sensor.convert\_temp()

Traceback (most recent call last):

&#x20; File "<stdin>", line 1

SyntaxError: invalid syntax

>>> >>> time.sleep\_ms(750)

Traceback (most recent call last):

&#x20; File "<stdin>", line 1

SyntaxError: invalid syntax

>>> >>> print("Temp:", sensor.read\_temp(roms\[0]), "C")

Traceback (most recent call last):

&#x20; File "<stdin>", line 1

SyntaxError: invalid syntax

>>> Temp: 23.5 C

Traceback (most recent call last):

&#x20; File "<stdin>", line 1

SyntaxError: invalid syntax

>>> >>> sensor.convert\_temp()

Traceback (most recent call last):

&#x20; File "<stdin>", line 1

SyntaxError: invalid syntax

>>> >>> time.sleep\_ms(750)

Traceback (most recent call last):

&#x20; File "<stdin>", line 1

SyntaxError: invalid syntax

>>> >>> print("Temp:", sensor.read\_temp(roms\[0]), "C")

Traceback (most recent call last):

&#x20; File "<stdin>", line 1

SyntaxError: invalid syntax

>>> Temp: 23.25 C

Traceback (most recent call last):

&#x20; File "<stdin>", line 1

SyntaxError: invalid syntax

>>> >>> sensor.convert\_temp sensor.read\_temp(roms\[0]),t\_temp()

Traceback (most recent call last):

&#x20; File "<stdin>", line 1

SyntaxError: invalid syntax

>>> >>> time.sleeproms\[0]), "C")

Traceback (most recent call last):

&#x20; File "<stdin>", line 1

SyntaxError: invalid syntax

>>> Temp: 22.75 ␛\[␛\[␛\[␛\[K

>>> sensor.convert\_temp()

>>> time.sleep\_ms(750)

>>> print("Temp:", sensor.read\_temp(roms\[0]), "C")

Temp: 21.4375 C

>>> sensor.convert\_temp()

>>> time.sleep\_ms(750)

>>> print("Temp:", sensor.read\_temp(roms\[0]), "C")

Temp: 8.3125 C

>>> sensor.convert\_temp()

>>> time.sleep\_ms(750)

>>> print("Ice bath:", sensor.read\_temp(roms\[0]), "C")

Ice bath: -0.375 C

```

