# pysmc3
Python library for SMC3

Asynchronous library for controlling SMC3 (Simulator Motor Controller) via a serial port. Su

## Prerequisites

The library requires 

## Usage

```python
from smc3 import Box, MotorNumber

loop = asyncio.get_event_loop()
box = Box(loop=loop, device="/dev/tty.usbdevice")
v = loop.run_until_complete(box.get_version())
print(f"SMC3 Version: {v / 100}")

motor = MotorNumber.A
box.enable_feedback(motor)
try:
    while 1:
        v = int(math.sin(time.clock_gettime(time.CLOCK_MONOTONIC)) * 512) + 512
        box.set_position(motor, v)
        loop.run_until_complete(asyncio.sleep(0.01))
except KeyboardInterrupt:
    box.disable_feedback()
    loop.run_until_complete(asyncio.sleep(1))


```
