import math

class Scroller:
    def __init__(self, text, offset, startpos, amplitude, font, draw_obj, width, velocity = -2):
        self.text = text
        self.draw = draw_obj
        self.amplitude = amplitude
        self.offset = offset
        self.velocity = velocity
        self.width = width
        self.startpos = startpos
        self.pos = startpos
        self.font = font
        self.maxwidth, unused = self.draw.textsize(self.text, font=self.font)

    def render(self):
        # Enumerate characters and draw them offset vertically based on a sine wave.
        x = self.pos
        
        for i, c in enumerate(self.text):
            # Stop drawing if off the right side of screen.
            if x > self.width:
                break

            # Calculate width but skip drawing if off the left side of screen.
            if x < -10:
                char_width, char_height = self.draw.textsize(c, font=self.font)
                x += char_width
                continue

            # Calculate offset from sine wave.
            y = self.offset + math.floor(self.amplitude * math.sin(x / float(self.width) * 2.0 * math.pi))

            # Draw text.
            self.draw.text((x, y), c, font=self.font, fill=255)

            # Increment x position based on chacacter width.
            char_width, char_height = self.draw.textsize(c, font=self.font)
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
