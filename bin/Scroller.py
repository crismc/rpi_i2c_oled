import math
import logging
from bin.Utils import Utils
class Scroller:
    default_amplitude = 0

    def __init__(self, text, startpos, font, display, amplitude = None, velocity = -2):
        self.text = text
        self.display = display
        self.velocity = velocity
        self.startpos = startpos
        self.pos = startpos
        self.font = font
        self.amplitude = amplitude if amplitude else Scroller.default_amplitude
        self.logger = logging.getLogger('Scroller')
        unused, self.height_offset = Utils.get_text_center(display, text, font) # height/4
        self.maxwidth, unused = Utils.get_text_size(display, text, font)

    def render(self):
        # Enumerate characters and draw them offset vertically based on a sine wave.
        x = self.pos
        for i, c in enumerate(self.text):
            # Stop drawing if off the right side of screen.
            if x > self.display.width:
                break

            # Calculate width but skip drawing if off the left side of screen.
            if x < -10:
                char_width, char_height = Utils.get_text_size(self.display, c, font=self.font)
                x += char_width
                continue

            # Calculate offset from sine wave.
            y = self.height_offset + math.floor(self.amplitude * math.sin(x / float(self.display.width) * 2.0 * math.pi))

            # Draw text.
            self.display.draw.text((x, y), c, font=self.font, fill=255)

            # Increment x position based on chacacter width.
            char_width, char_height = Utils.get_text_size(self.display, c, font=self.font)
            x += char_width

    def move_for_next_frame(self, allow_startover):
        self.pos += self.velocity
        # Start over if text has scrolled completely off left side of screen.
        if self.has_completed():
            if allow_startover:
                self.start_over()
                return True
            else:
                return False
        return True

    def start_over(self):
        self.pos = self.startpos

    def has_completed(self):
        return self.pos < -self.maxwidth
