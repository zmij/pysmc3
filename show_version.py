#!/usr/bin/env python3

import asyncio
import argparse
import logging

from smc3 import Box, DEFAULT_BAUDRATE

logging.basicConfig(
    level=logging.INFO, format="%(name)10s - %(levelname)7s - %(message)s"
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-b", "--baudrate", type=int, default=DEFAULT_BAUDRATE, help="UART baud rate"
    )
    parser.add_argument("device", help="USB device")
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    box = Box(loop=loop, device=args.device, baudrate=args.baudrate)

    res = loop.run_until_complete(box.get_version_async())
    print(res / 100)


if __name__ == "__main__":
    main()
