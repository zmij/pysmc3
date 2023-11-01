#!/usr/bin/env python3

import asyncio
import argparse
import logging

from termcolor import colored, cprint

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
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    box = Box(loop=loop, device=args.device, baudrate=args.baudrate)
    v = loop.run_until_complete(box.get_version_async())
    cprint(f"SMC3 Version: {v / 100}", "red")

    for m in MotorNumber.__members__.values():
        cprint(f"Motor {m.name}", "cyan", attrs=["bold"])
        for p in [Parameter.Kp, Parameter.Ki, Parameter.Kd, Parameter.Ks]:
            v = loop.run_until_complete(box.read_param_async(m, p))
            cprint(f"  {p.name}: {v[0]/100}", attrs=["bold"])

        for p in [Parameter.MinMax, Parameter.PWMinMax, Parameter.FBDeadZone]:
            v = loop.run_until_complete(box.read_param_async(m, p))
            cprint(f"  {p.name}: {v}", attrs=["bold"])

        v = loop.run_until_complete(box.read_param_async(m, Parameter.Position))
        cprint(f"  Position", "blue", attrs=["bold"])
        cprint(f"    target:   {v[0]}", "blue", attrs=["bold"])
        cprint(f"    feedback: {v[1]}", "blue", attrs=["bold"])

        v = loop.run_until_complete(box.read_param_async(m, Parameter.PwmStatus))
        cprint(f"  pwm:    {v[0]}", "magenta", attrs=["bold"])
        cprint(f"  status: {v[1]}", "red", attrs=["bold"])


if __name__ == "__main__":
    main()
