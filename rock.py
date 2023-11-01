#!/usr/bin/env python3

import asyncio
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
    parser.add_argument("-s", "--sideways", action="store_true", help="Scale time")
    parser.add_argument("device", help="USB device")
    args = parser.parse_args()

    box = Box(device=args.device, baudrate=args.baudrate)
    v = box.get_version()
    cprint(f"SMC3 Version: {v / 100}", "red")

    try:
        while 1:
            t = time.clock_gettime(time.CLOCK_MONOTONIC)
            a = int(math.sin(t) * 512) + 512
            b = args.sideways and a or 1024 - a
            box.set_position(MotorNumber.A, a)
            box.set_position(MotorNumber.B, b)
            box.delay(0.01)
    except KeyboardInterrupt:
        box.delay(1)


if __name__ == "__main__":
    main()
