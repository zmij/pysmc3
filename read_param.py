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
    parser.add_argument("param", help="Param (as in protocol)")
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    box = Box(loop=loop, device=args.device, baudrate=args.baudrate)

    if len(args.param) != 1:
        raise ValueError(f"Params are singe-char only")

    try:
        res = loop.run_until_complete(
            box._client.make_read_request(
                bytes(f"[rd{args.param}]", "ascii"), args.param
            )
        )
        print(f"Motor {res[0].name} {res[1].name} {res[2:]}")
    except TimeoutError:
        print("Request timeout")


if __name__ == "__main__":
    main()
