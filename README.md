# pysmc3 - Python Library for SMC3 Motor Controllers

## Table of Contents

- [About](#about)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
  - [Examples](#examples)
- [Limitations](#limitations)
- [Contributing](#contributing)
- [License](#license)

## About

`pysmc3` is a Python library designed to interact with [SMC3](https://github.com/SimulatorMotorController/SMC3), an Arduino-based software for controlling 3-DOF motion simulators used in gaming. This library provides an alternative to the existing diagnostic tools, which are only available for Windows. The library offers a convenient abstraction of the control box, allowing you to read and write parameters as well as set motor positions.

## Features

- Abstraction of the SMC3 control box through the `smc3.Box` class.
- Asynchronous communications supported by asyncio.
- Methods to read and write parameters for the control box.
- Methods to set motor positions with ease.

## Prerequisites

- Python 3.x

## Installation

Clone the GitHub repository and install the required dependencies:

```bash
git clone https://github.com/zmij/pysmc3.git
cd pysmc3
pip install -r requirements.txt
```

## Dependencies

* asyncio
* serial_asyncio
* termcolor (for example programs)

## Usage

Here's a quick example snippet that demonstrates how to move Motor A on a sine wave:

```python
from smc3 import Box, MotorNumber
import math
import time

box = Box(device="/dev/tty.usbdevice")
print(f"SMC3 Version: {box.get_version() / 100}")

motor = MotorNumber.A
box.enable_feedback(motor)
try:
    while True:
        v = int(math.sin(time.clock_gettime(time.CLOCK_MONOTONIC)) * 512) + 512
        box.set_position(motor, v)
        box.delay(0.01)
except KeyboardInterrupt:
    box.disable_feedback()
    box.delay(1)
```

### Examples

The repository includes several example programs:

- `show_version.py`: Displays the SMC3 version number.
- `show_status.py`: Shows PID settings for all motors and their current status.
- `sine.py`: Moves a single motor on a sine wave.
- `rock.py`: Rocks the motion simulator back and forth or side to side.
- `puke.py`: Moves all three motors on a sine wave with a phase shift of 2π/3.

## Limitations

While the library has been tested on a MacBook connected to a control box from the DOFReality company, further testing is required to identify potential issues.

## Contributing

Feel free to fork the repository and send pull requests. All contributions are welcome!

## License

Licensed under the [Apache License, Version 2.0](LICENSE.md).
