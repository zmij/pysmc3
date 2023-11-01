#!/usr/bin/env python3

import argparse
import logging
import math
import time

from termcolor import cprint

from smc3 import Box, MotorNumber, DEFAULT_BAUDRATE

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)-8s - %(levelname)-7s - %(message)s",
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-b", "--baudrate", type=int, default=DEFAULT_BAUDRATE, help="UART baud rate"
    )
    parser.add_argument("device", help="USB device")
    parser.add_argument("motor", choices=["A", "B", "C"], help="Motor to monitor")
    args = parser.parse_args()

    box = Box(device=args.device, baudrate=args.baudrate)
    v = box.get_version()
    cprint(f"SMC3 Version: {v / 100}", "red")

    motor = MotorNumber.__members__[args.motor]
    box.enable_feedback(motor)
    try:
        while 1:
            v = int(math.sin(time.clock_gettime(time.CLOCK_MONOTONIC)) * 512) + 512
            box.set_position(motor, v)
            box.delay(0.01)
    except KeyboardInterrupt:
        box.disable_feedback()
        box.delay(1)


if __name__ == "__main__":
    main()
