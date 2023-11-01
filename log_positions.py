#!/usr/bin/env python3

import asyncio
import argparse
import logging

from termcolor import colored, cprint

from smc3 import Box, MotorNumber, Parameter, DEFAULT_BAUDRATE

logging.basicConfig(
    level=logging.DEBUG,
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

    loop = asyncio.get_event_loop()
    box = Box(loop=loop, device=args.device, baudrate=args.baudrate)
    v = loop.run_until_complete(box.get_version_async())
    cprint(f"SMC3 Version: {v / 100}", "red")

    box.enable_feedback(MotorNumber.__members__[args.motor])
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        box.disable_feedback()
        loop.run_until_complete(asyncio.sleep(1))


if __name__ == "__main__":
    main()
