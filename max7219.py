from micropython import const
import framebuf
from utime import sleep_ms
import uasyncio as asyncio
from font_5x7 import FONT_5x7

_NOOP = const(0)
_DIGIT0 = const(1)
_DECODEMODE = const(9)
_INTENSITY = const(10)
_SCANLIMIT = const(11)
_SHUTDOWN = const(12)
_DISPLAYTEST = const(15)

class Matrix8x8:
    def __init__(self, spi, cs, num):
        self.spi = spi
        self.cs = cs
        self.cs.init(cs.OUT, True)
        self.buffer = bytearray(8 * num)
        self.num = num
        fb = framebuf.FrameBuffer(self.buffer, 8 * num, 8, framebuf.MONO_HLSB)
        self.framebuf = fb
        self.fill = fb.fill
        self.pixel = fb.pixel
        self.hline = fb.hline
        self.vline = fb.vline
        self.line = fb.line
        self.rect = fb.rect
        self.fill_rect = fb.fill_rect
        self.blit = fb.blit
        self.init()

    def _write(self, command, data):
        self.cs(0)
        for m in range(self.num):
            self.spi.write(bytearray([command, data]))
        self.cs(1)

    def init(self):
        for command, data in (
            (_SHUTDOWN, 0),
            (_DISPLAYTEST, 0),
            (_SCANLIMIT, 7),
            (_DECODEMODE, 0),
            (_INTENSITY, 15),
            (_SHUTDOWN, 1),
        ):
            self._write(command, data)

    def brightness(self, value):
        if not 0 <= value <= 15:
            raise ValueError("Brightness out of range")
        self._write(_INTENSITY, value)

    def show(self):
        for y in range(8):
            self.cs(0)
            for m in range(self.num):
                self.spi.write(bytearray([_DIGIT0 + y, self.buffer[(y * self.num) + m]]))
            self.cs(1)

    def text(self, message, xpos=0, ypos=0, color=1):
        """Render text using FONT_5x7 onto the matrix."""
        self.fill(0)
        x_offset = xpos
        for char in message:
            self.draw_char(char, x_offset, ypos, color)
            x_offset += 6  # Move to the next character position
        self.show()

    def draw_char(self, char, x, y, color=1):
        """Draw a single character from FONT_5x7 at (x, y) position."""
        char_data = FONT_5x7.get(char, FONT_5x7[' '])  # Default to space if char not in font
        for col, byte in enumerate(char_data):
            for row in range(7):  # 7 rows in FONT_5x7
                if (byte >> row) & 1:
                    self.pixel(x + col, y + row, color)

    def scroll(self, text, delay=10, distance=None, prefix='  '):
        text = prefix + text
        if not distance:
            distance = len(text) * 8
        for i in range(distance):
            self.text(text, -i)
            sleep_ms(delay)

    async def async_scroll(self, text, delay=10, distance=None, prefix='  '):
        text = prefix + text
        if not distance:
            distance = len(text) * 8
        for i in range(distance):
            self.text(text, -i)
            await asyncio.sleep_ms(delay)

