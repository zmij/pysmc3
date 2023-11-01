#!/usr/bin/env python3

import argparse
import logging

from termcolor import cprint

from smc3 import Box, MotorNumber, Parameter, DEFAULT_BAUDRATE

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
    parser.add_argument("position", type=int, help="Target position (0-1024)")
    args = parser.parse_args()

    if args.position < 0 or 1024 < args.position:
        raise ValueError(f"Invalid motor position {args.position}")

    box = Box(device=args.device, baudrate=args.baudrate)
    v = box.get_version()
    cprint(f"SMC3 Version: {v / 100}", "red")

    motor = MotorNumber.__members__[args.motor]
    box.enable_feedback(motor)
    try:
        box.set_position(motor, args.position)
        box.delay(2)
    except KeyboardInterrupt:
        box.disable_feedback()
        box.delay(1)


if __name__ == "__main__":
    main()
