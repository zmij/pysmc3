import asyncio
import serial_asyncio
import logging

from typing import Any, List
from serial import EIGHTBITS, PARITY_NONE, STOPBITS_ONE

from .loggable import Loggable
from .protocol import Client, Protocol, Motor, Parameter, set_command, DEFAULT_BAUDRATE


class MotorStatus:
    motor: Motor
    target: int
    feedback: int
    pwm: int
    status: int

    def __init__(
        self,
        motor: Motor,
        *,
        target: int = 0,
        feedback: int = 0,
        pwm: int = 0,
        status: int = 0,
    ) -> None:
        self.motor = motor
        self.target = target
        self.feedback = feedback
        self.pwm = pwm
        self.status = status

    def __str__(self) -> str:
        return f"{self.motor.name} target {self.target:3d} feedback {self.feedback:3d} pwm {self.pwm:3d} status {self.status}"


"""
Interface Type - Serial
ComPort = the Arduino ComPort, you can find it in Windows Device Manager.
BitsPerSec - 500000
Data Bits - 8
Parity - None
Stop Bit -1
Output Bit Range - 10
Output Type - Binary
"""


class Box(Loggable):
    """
    Class representing the Simulator Motor Control box
    """

    _loop: asyncio.AbstractEventLoop
    _client: Client
    _motors: List[MotorStatus]

    def __init__(
        self,
        *,
        device: str,
        loop: asyncio.AbstractEventLoop = None,
        baudrate: int = DEFAULT_BAUDRATE,
    ) -> None:
        super().__init__()
        self.set_logger(logging.getLogger("BOX"))

        if not loop:
            loop = asyncio.get_event_loop()

        self._loop = loop
        self._client = Client(
            loop,
            position_cb=self._position_received,
            pwm_status_cb=self._pwm_status_received,
        )
        self._motors = [
            MotorStatus(Motor.A),
            MotorStatus(Motor.B),
            MotorStatus(Motor.C),
        ]
        proto = Protocol(self._client)
        _, _ = loop.run_until_complete(
            serial_asyncio.create_serial_connection(
                loop,
                lambda: proto,
                device,
                baudrate=baudrate,
                bytesize=EIGHTBITS,
                parity=PARITY_NONE,
                stopbits=STOPBITS_ONE,
            )
        )

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        return self._loop

    async def get_version_async(self) -> int:
        packet = await self._client.make_read_request(b"[ver]", "v")
        return packet[2]

    def get_version(self) -> int:
        return self._loop.run_until_complete(self.get_version_async())

    async def read_param_async(self, motor: Motor, param: Parameter) -> Any:
        _, _, *args = await self._client.read_parameter(motor, param)
        return args

    def read_param(self, motor: Motor, param: Parameter) -> Any:
        return self._loop.run_until_complete(self.read_param_async(motor, param))

    def delay(self, delay: float) -> None:
        self._loop.run_until_complete(asyncio.sleep(delay))

    def save_settings(self) -> None:
        self._client.send_command(b"[sav]")

    def enable_feedback(self, motor: Motor) -> None:
        self.log_info(f"Enable feedback for {motor.name} {motor.value}")
        self._client.send_command(bytes(f"[mo{motor.value}]", "ascii"))

    def enable_motor(self, motor: Motor) -> None:
        self._client.send_command(bytes(f"[en{motor.value}]", "ascii"))

    def enable_motors(self) -> None:
        self._client.send_command(b"[ena]")

    def disable_feedback(self) -> None:
        self.log_info(f"Disable feedback for motors")
        self._client.send_command(b"[mo0]")

    def set_position(self, motor: Motor, pos: int) -> None:
        self._client.send_command(set_command(motor, Parameter.Position, pos))

    def set_parameter(self, motor: Motor, param: Parameter, *args) -> None:
        self._client.send_command(set_command(motor, param, *args))

    def _position_received(self, motor: Motor, target: int, feedback: int) -> None:
        ms = self._motors[motor.value - 1]
        ms.target = target
        ms.feedback = feedback
        self.log_info(ms)

    def _pwm_status_received(self, motor: Motor, pwm: int, status: int) -> None:
        ms = self._motors[motor.value - 1]
        ms.pwm = pwm
        ms.status = status
        self.log_info(ms)
