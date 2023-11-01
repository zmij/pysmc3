"""
Packet Sent            Description                                                                                              Response Packet
-------------------------------------------------------------------------------------------------------------------------------------------
[Axx],[Bxx],[Cxx]  Send position updates for Motor 1,2,3 where xx is the binary position limitted to range 0-1024            None
[Dxx],[Exx],[Fxx]  Send the Kp parameter for motor 1,2,3 where xx is the Kp binary value (restrict to 0 - 1000)              None
[Gxx],[Hxx],[Ixx]  Send the Ki parameter for motor 1,2,3 where xx is the Ki binary value (restrict to 0 - 1000)              None
[Jxx],[Kxx],[Lxx]  Send the Kd parameter for motor 1,2,3 where xx is the Kd binary value (restrict to 0 - 1000)              None
[Mxx],[Nxx],[Oxx]  Send the Ks parameter for motor 1,2,3 where xx is the Ks (d term smoothing parameter between 1 and 20)    None
[Pxy],[Qxy],[Rxy]  Send the PWMmin and PWMmax values x is the PWMmin and y is PWMmax each being in range 0-255              None
                    PWMmax should always be greater than or equal to PWMmin
[Sxy],[Txy],[Uxy]  Send the Motor Min/Max Limits (x) and Input Min/Max Limits (y) (Note same value used for Min and Max)    None
[Vxy],[Wxy],[Xxy]  Send the Feedback dead zone (x) and the PWM reverse duty (y) for each motor                              None
[mo1],[mo2],[mo3]  Request continous motor position, feedback, pwm and status data (all packets sent every 15ms)            [Axy][Bxy][Cxy][axy][bxy][cxy]
[mo0]              Disable continuous feedback from previous [mo1],[mo2], or [mo3] command                                  None
[ena]              Enable all motors                                                                                        None
[sav]              Save parameters to non-volatile memory                                                                    None
[ver]              Request the SMC3 software version, returned value is mult by 100.  (ie: 101 is ver 1.01)                  [vyy]
[rdA],[rdB],[rdC]  Request motor target and feedback for Motor 1,2, or 3 parameters scaled 0-255.                            [Axy][Bxy][Cxy]
[rda],[rdb],[rdc]  Request motor pwm and status data for Motor 1,2, or 3 parameters scaled 0-255.                            [Axy][Bxy][Cxy]
[rdD],[rdE],[rdF]  Request the Kp parameter for motor 1,2,3 where xx is the Kp value multiplied by 100                      [Dxx][Exx][Fxx]
[rdG],[rdH],[rdI]  Request the Ki parameter for motor 1,2,3 where xx is the Ki value multiplied by 100                      [Gxx][Hxx][Ixx]
[rdJ],[rdK],[rdL]  Request the Kd parameter for motor 1,2,3 where xx is the Kd value multiplied by 100                      [Jxx][Kxx][Lxx]


Note the Arduino SMC3 code does not check values sent are within valid ranges.  It is the job of the host application to keep values within
sensible limits as recommended above.
"""

import asyncio
import logging
import datetime

from enum import Enum
from typing import Tuple, Any, Dict, Callable

from .loggable import Loggable

PACKET_LEN = 5
BYTE_ORDER = "big"

DEFAULT_BAUDRATE = 500000
DEFAULT_TIMEOUT = datetime.timedelta(seconds=1)


class Motor(Enum):
    A = 1
    B = 2
    C = 3


class Parameter(Enum):
    Unknown = ""
    Position = "A"
    Kp = "D"
    Ki = "G"
    Kd = "J"
    Ks = "M"
    PWMinMax = "P"
    MinMax = "S"
    FBDeadZone = "V"
    PwmStatus = "a"
    Version = "v"

    def __init__(self, v: str):
        self.code = v

    @classmethod
    def _missing_(cls, value):
        p = Parameter.__new__(Parameter, "")
        p.code = value
        return p


READ_ONLY_PARAMS = [Parameter.PwmStatus, Parameter.Version]

COMMAND_ARGC = {
    Parameter.PWMinMax: 2,
    Parameter.MinMax: 2,
    Parameter.FBDeadZone: 2,
}

COMMAND_ARG_LIMITS = {
    Parameter.Position: (0, 1024),
    Parameter.Kp: (0, 1000),
    Parameter.Ki: (0, 1000),
    Parameter.Kd: (0, 1000),
    Parameter.Ks: (1, 20),
}

PARAM_VALUE_COUNT = {
    Parameter.Position: 2,
    Parameter.PwmStatus: 2,
    Parameter.MinMax: 2,
    Parameter.PWMinMax: 2,
    Parameter.FBDeadZone: 2,
}


def param_to_char(motor: Motor, param: Parameter) -> str:
    return chr(ord(param.value) + motor.value - 1)


def char_to_param(char: str) -> Tuple[Motor, Parameter]:
    return byte_to_param(ord(char))


def byte_to_param(byte: int) -> Tuple[Motor, Parameter]:
    start = ord("A")
    if byte >= ord("a"):
        start = ord("a")
    motor = Motor((byte - start) % 3 + 1)
    param = Parameter(chr((byte - start) // 3 * 3 + start))
    return motor, param


def read_command(motor: Motor, param: Parameter) -> bytes:
    return bytes(f"[rd{param_to_char(motor, param)}]", "ascii")


def set_command(motor: Motor, param: Parameter, *args) -> bytes:
    argc = 1
    if param in READ_ONLY_PARAMS:
        raise TypeError(f"Paramenter {param.name} is read-only")
    if param in COMMAND_ARGC:
        argc = COMMAND_ARGC[param]
    if len(args) != argc:
        raise TypeError(
            f"Invalid argument count for parameter {param.name}, got {len(args)} required {argc}"
        )
    limits = param in COMMAND_ARG_LIMITS and COMMAND_ARG_LIMITS[param] or None

    if argc == 2:
        limits = (0, 255)
    if limits:
        for a in args:
            if a < limits[0] or limits[1] < a:
                raise ValueError(
                    f"Value {a} out of range {limits} for param {param.name}"
                )

    return format_value(param_to_char(motor, param), *args)


def format_value(code: str, *args) -> bytes:
    argc = len(args)
    if argc < 1 or 2 < argc:
        raise ValueError(f"Invalid number of values {argc}")
    cmd = bytes(f"[{code}", "ascii")
    if argc == 1:
        cmd = cmd + args[0].to_bytes(2, BYTE_ORDER) + b"]"
    elif argc == 2:
        cmd = cmd + args[0].to_bytes() + args[1].to_bytes() + b"]"
    return cmd


def parse_packet(packet: bytes) -> Tuple[Motor, Parameter]:
    if len(packet) != PACKET_LEN:
        raise ValueError(f"Invalid packet size {len(packet)}")
    motor, param = byte_to_param(packet[1])
    value_count = 1
    if param in PARAM_VALUE_COUNT:
        value_count = PARAM_VALUE_COUNT[param]
    if value_count == 1:
        return (
            chr(packet[1]),
            motor,
            param,
            int.from_bytes(packet[2:4], byteorder=BYTE_ORDER, signed=False),
        )
    elif value_count == 2:
        return chr(packet[1]), motor, param, packet[2], packet[3]
    raise ValueError(f"Invalid value count setup for param {param.name}: {value_count}")


class Client(Loggable):
    _loop: asyncio.AbstractEventLoop
    _transport: asyncio.Transport
    _outstanding: Dict[str, asyncio.Future]

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        position_cb: Callable[[Motor, int, int], None] = None,
        pwm_status_cb: Callable[[Motor, int, int], None] = None,
    ) -> None:
        super().__init__()
        self.set_logger(logging.getLogger("CLIENT"))
        self._loop = loop
        self._transport = None
        self._outstanding = dict[str, asyncio.Future]()
        self._position_cb = position_cb
        self._pwm_status_sb = pwm_status_cb

    def send_command(self, cmd: bytes) -> None:
        self._transport.write(cmd)

    async def wait_for_packet(
        self,
        packet_type: str,
        timeout: datetime.timedelta = DEFAULT_TIMEOUT,
    ) -> Any:
        if packet_type in self._outstanding:
            self.log_warning(f"Already waiting for packet `{packet_type}`")
        fut = self._loop.create_future()
        self._outstanding[packet_type] = fut
        return await asyncio.wait_for(fut, timeout.total_seconds())

    async def read_parameter(
        self,
        motor: Motor,
        param: Parameter,
        timeout: datetime.timedelta = DEFAULT_TIMEOUT,
    ) -> Any:
        return await self.make_read_request(
            read_command(motor, param), param_to_char(motor, param), timeout=timeout
        )

    async def make_read_request(
        self,
        cmd: bytes,
        wait_for: str,
        timeout: datetime.timedelta = DEFAULT_TIMEOUT,
    ) -> Any:
        self.send_command(cmd)
        return await self.wait_for_packet(wait_for, timeout=timeout)

    def packet_recieved(
        self, packet_type: str, motor: Motor, param: Parameter, *args
    ) -> None:
        self.log_debug(f"Received packet '{packet_type}' {motor} {param} {args}")
        if packet_type in self._outstanding:
            self._outstanding[packet_type].set_result((motor, param, *args))
            del self._outstanding[packet_type]
        # Check for position and status callback
        elif param == Parameter.Position:
            if self._position_cb:
                self._position_cb(motor, args[0], args[1])
        elif param == Parameter.PwmStatus:
            if self._pwm_status_sb:
                self._pwm_status_sb(motor, args[0], args[1])


class Protocol(asyncio.Protocol, Loggable):
    def __init__(self, client: Client):
        super().__init__()
        self.set_logger(logging.getLogger("PROTO"))

        self._transport = None
        self._client = client
        self._buffer = bytes()

    def connection_made(self, transport) -> None:
        self._transport = transport
        self._client._transport = transport
        self.log_debug(f"port opened {self._transport}")

    def data_received(self, data) -> None:
        self.log_debug(f"data received {repr(data)}")
        if not data:
            return
        self._buffer = self._buffer + data
        self.process_buffer()

    def process_buffer(self) -> None:
        if len(self._buffer) < 5:
            return

        buffer = self._buffer[:5]
        packet = parse_packet(buffer)
        self._client.packet_recieved(*packet)

        self._buffer = self._buffer[5:]
        self.process_buffer()

    def connection_lost(self, exc) -> None:
        self.log_debug("port closed")
        self._transport.loop.stop()

    def pause_writing(self) -> None:
        self.log_debug("pause writing")
        self.log_debug(self._transport.get_write_buffer_size())

    def resume_writing(self) -> None:
        self.log_debug(self._transport.get_write_buffer_size())
        self.log_debug("resume writing")
