#!/usr/bin/env python3

import logging
import random
import time
import os, pty
from threading import Thread

from smc3.protocol import format_value, read_command, param_to_char, Motor, Parameter

logging.basicConfig(level=logging.DEBUG, format="%(levelname)s - %(message)s")

logger = logging.getLogger(__name__)


class Stub:
    def __init__(
        self,
        *,
        receive_bytes: bytes,
        send_bytes: bytes = None,
        send_fn=None,
        match_fn=None,
    ):
        self.__receive_bytes = receive_bytes
        self.__send_bytes = send_bytes
        self.__calls = 0

        if (send_bytes is None) == (send_fn is None):
            raise TypeError("Specify either send_bytes or send_fn.")

        if send_bytes is not None:
            self.__send_fn = lambda *_: send_bytes
        else:
            self.__send_fn = send_fn

    def __lt__(self, other) -> bool:
        return len(self.receive_bytes) < len(other.receive_bytes)

    @property
    def receive_bytes(self) -> bytes:
        return self.__receive_bytes

    def call(self):
        self.__calls += 1
        return self.__send_fn(self.__calls)

    def matches(self, buffer: bytes) -> bool:
        return buffer.startswith(self.__receive_bytes)

    def consume(self, buffer: bytes) -> bytes:
        return buffer[len(self.__receive_bytes) :]

    @property
    def calls(self) -> int:
        return self.__calls

    @property
    def called(self) -> bool:
        return self.calls > 0

    def __repr__(self) -> str:
        if self.__send_bytes:
            return f"{self.receive_bytes} => {self.__send_bytes}"
        else:
            return f"{self.receive_bytes} => fn()"


class MockSerial:
    QUIT_SIGNAL = b"mockserialquit"

    def __init__(self):
        self.__master, self._slave = pty.openpty()
        self.__stubs = {}
        self.__thread = Thread(target=self.__receive, daemon=True)

    @property
    def port(self):
        return os.ttyname(self._slave)

    @property
    def stubs(self):
        return self.__stubs

    def stub(self, *, name=None, **kwargs):
        new_stub = Stub(**kwargs)
        self.__stubs[name or new_stub.receive_bytes] = new_stub
        return new_stub

    def __match(self, buffer):
        potential_matches = [
            stub for stub in self.stubs.values() if stub.matches(buffer)
        ]

        if len(potential_matches) > 1:
            logger.debug(f"Potential matches: {sorted(potential_matches)}.")

            return None

        matches = sorted(
            (stub for stub in self.stubs.values() if stub.matches(buffer)),
            reverse=True,
        )

        return matches[0] if matches else None

    def __reply(self, buffer):
        if not buffer:
            return buffer

        stub = self.__match(buffer)

        if not stub:
            return buffer

        send_bytes = stub.call()
        logger.debug(f"Match stub: {stub}.")

        if send_bytes:
            os.write(self.__master, send_bytes)
            logger.debug(f"Buffer write: {send_bytes}.")
        else:
            logger.debug(f"Discard buffer.")

        buffer = stub.consume(buffer)
        return self.__reply(buffer)

    def __receive(self):
        buffer = bytes()

        while self.QUIT_SIGNAL not in buffer:
            # read a good chunk of data each time
            buffer += os.read(self.__master, 32)
            logger.debug(f"Buffer read: {buffer}.")
            buffer = self.__reply(buffer)

        logger.debug("Detached mock serial port.")

    def send(self, buffer):
        os.write(self.__master, buffer)
        logger.debug(f"Buffer write: {buffer}.")

    def open(self):
        self.__thread.start()
        logger.debug(f"Attached to mock serial port {self.port}.")

    def close(self):
        logger.debug("Detaching mock serial port.")

        # stop the thread trying to read from it
        os.write(self._slave, self.QUIT_SIGNAL)
        self.__thread.join(timeout=1)

        if self.__thread.is_alive():
            logger.warning("Unable to detach mock serial port.")

        tmp_thread = Thread(
            # may hang if thread still reading from it
            target=lambda: os.close(self.__master),
            daemon=True,
        )

        logger.debug("Closing mock serial port.")
        tmp_thread.start()
        tmp_thread.join(timeout=1)

        if tmp_thread.is_alive():
            logger.warning("Unable to close mock serial port.")
            return

        os.close(self._slave)
        logger.debug("Closed mock serial port.")


if __name__ == "__main__":
    device = MockSerial()
    device.stub(
        name="version", receive_bytes=b"[ver]", send_bytes=format_value("v", 101)
    )
    for m in Motor.__members__.values():
        device.stub(
            name=f"Motor {m.name} target and feedback",
            receive_bytes=read_command(m, Parameter.Position),
            send_bytes=format_value(param_to_char(m, Parameter.Position), 100, 10),
        )
        device.stub(
            name=f"Motor {m.name} pwm and status",
            receive_bytes=read_command(m, Parameter.PwmStatus),
            send_bytes=format_value(param_to_char(m, Parameter.PwmStatus), 200, 13),
        )
        for p in [Parameter.Kp, Parameter.Ki, Parameter.Kd, Parameter.Ks]:
            val = random.randrange(100, 2000)
            device.stub(
                name=f"Motor {m.name} {p.name}",
                receive_bytes=read_command(m, p),
                send_bytes=format_value(param_to_char(m, p), val),
            )
        device.stub(
            name=f"Motor {m.name} position command",
            receive_bytes=bytes(
                f"[{param_to_char(m, Parameter.Position)}^@^@]", "ascii"
            ),
            send_bytes=b"",
        )
        device.stub(
            name=f"Motor {m.name} pwm command",
            receive_bytes=bytes(
                f"[{param_to_char(m, Parameter.PwmStatus)}^@^@]", "ascii"
            ),
            send_bytes=b"",
        )

    device.open()
    print(device.port)
    print(device.__dict__)
    try:
        while 1:
            time.sleep(100 / 1000)
            device.send(
                b"[A\x00\x00][B\x00\x00][C\x00\x00][a\x00\x00][b\x00\x00][c\x00\x00]"
            )
    finally:
        device.close()
