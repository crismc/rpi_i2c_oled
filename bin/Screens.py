import logging
import textwrap
import time

from PIL import Image, ImageDraw, ImageFont, ImageOps

from bin.Scroller import Scroller
from bin.SSD1306 import SSD1306_128_32 as SSD1306
from bin.Utils import Utils


class Display:
    DEFAULT_BUSNUM = 1
    SCREENSHOT_PATH = "./img/examples/"

    def __init__(self, busnum = None, screenshot = False, rotate = False, show_icons = True,
                 compact = False, show_hint = False):
        self.logger = logging.getLogger('Display')

        if not isinstance(busnum, int):
            busnum = Display.DEFAULT_BUSNUM

        self.display = SSD1306(busnum)
        self.clear()
        self.width = self.display.width
        self.height = self.display.height
        self.rotate = rotate

        self.compact = compact
        self.show_icons = show_icons
        self.show_hint = show_hint
        self.hint_right = True

        if self.show_icons and self.show_hint:
           self.logger.error("show_icons and show_hint both True; turning off hint")
           self.show_hint = False

        self.image = Image.new("1", (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)
        self.screenshot = screenshot

    def clear(self):
        self.display.begin()
        self.display.clear()
        self.display.display()

    def prepare(self):
        self.draw.rectangle((0, 0, self.width, self.height), outline = 0, fill = 0)

    def show(self):
        if isinstance(self.rotate, int):
            self.image = self.image.rotate(self.rotate)
            self.draw = ImageDraw.Draw(self.image)

        self.display.image(self.image)
        self.display.display()

    def capture_screenshot(self, name):
        if self.screenshot:
            if isinstance(self.screenshot, str):
                dir = self.screenshot
            else:
                dir = Display.SCREENSHOT_PATH

            path = dir.rstrip('/') + '/' + name.lower() + '.png'
            self.logger.info("saving screenshot to '" + path + "'")
            self.image.save(path)

class BaseScreen:
    font_path = Utils.current_dir + "/fonts/DejaVuSans.ttf"
    font_bold_path = Utils.current_dir + "/fonts/DejaVuSans-Bold.ttf"
    fonts = {}

    def __init__(self, duration, display = Display(), utils = Utils(), config = None):
        self.display = display
        self.duration = duration
        self.utils = utils
        self.config = config
        self.hint = None
        self.icon = None
        self.font_size = 8
        self.logger = logging.getLogger('Screen')
        self.logger.info("'" + self.__class__.__name__ + "' created")

    @property
    def name(self):
        return str(self.__class__.__name__).lower().replace("screen", "")

    def set_icon(self, path):
        """ set the image for this screen """
        if not self.icon or self.icon_path != path:
           self.icon_path = path
           img = Image.open(r"" + Utils.current_dir + self.icon_path)
           # img = img.convert('RGBA') # MUST be in RGB mode for the OLED
           # invert black icon to white (255) for OLED display
           #self.icon = ImageOps.invert( self.icon )
           self.icon = img.resize([30, 30])


    @property
    def text_indent(self):
        """ :return: how far to indent a line of text for this screen """
        if self.display.show_icons and self.icon:
            return 29
        elif self.hint and not self.display.hint_right:
            return 16
        return 0

    def capture_screenshot(self, name = None):
        if not name:
            name = self.name
        self.display.capture_screenshot(name)

    def display_text(self, text_lines):
        """ Display multiple lines of text with auto-resizing/positioning
            of the text based on the passed in text. """
        if not text_lines:
           return

        # set the number of lines, which reconfigures fonts
        self.set_text_lines(len(text_lines))
        font = self.font()

        line = 0
        for text in text_lines:
           # display the text line at the correct x / y based on config
           x = self.text_indent
           y = self.text_y[line]
           self.display.draw.text((x, y), text, font=font, fill=255)

           line += 1
           if line >= 3:
              return # too many lines passed in!

    def set_text_lines(self, num_lines):
       """ Set the number of text lines that will be displayed. """
       self.text_lines = num_lines

       # set defaults based on number of lines
       if self.text_lines > 2:
          if self.text_indent < 10:
             self.font_size = 10
          else:
             self.font_size = 9
       else:
          if self.text_indent < 10:
             self.font_size = 14
          else:
             self.font_size = 13

    @property
    def text_y(self):
        if self.text_lines == 1:
           return [0]
        elif self.text_lines == 2:
           return [0, 18]
        elif self.text_lines == 3:
           return [0, 11, 21]
        else:
           return None

    def display_hint(self):
       if not self.hint or not self.display.show_hint:
           return

       # determine whether to put hints on right or left
       x_pos = 0
       if self.display.hint_right:
          x_pos = 119
       font = self.font(size=11, is_bold=True)

       draw = self.display.draw
       draw.rectangle((x_pos, 0, x_pos + 10, 32), outline = 255, fill = 255)

       # display the text based on how many characters the hint is
       text_fill = 0
       draw.text((x_pos, -2), self.hint[0], font=font, fill=text_fill)
       if (len(self.hint) > 1):
           draw.text((x_pos, 8), self.hint[1], font=font, fill=text_fill)
       if (len(self.hint) > 2):
           draw.text((x_pos, 18), self.hint[2], font=font, fill=text_fill)

    def font(self, size = None, is_bold = False):
        # default to the current screen's font size if none provided
        if not size:
           size = self.font_size

        suffix = None
        if is_bold:
            suffix = '_bold'

        key = 'font_{}{}'.format(str(size), suffix)

        if key not in BaseScreen.fonts:
            font = BaseScreen.font_path
            if is_bold:
                font = BaseScreen.font_bold_path

            font = ImageFont.truetype(font, int(size))
            BaseScreen.fonts[key] = font
        return BaseScreen.fonts[key]

    @property
    def default_message(self):
        return 'Welcome to ' + self.utils.get_hostname()

    # helper function to display the current page (used by standard screens)
    def render_with_defaults(self):
        self.display_hint()

        # add icon to canvas (if enabled)
        if self.display.show_icons and self.icon:
           self.display.image.paste(self.icon, (-3, 3))

        self.capture_screenshot()
        self.display.show()
        time.sleep(self.duration)

    def render(self):
        self.display.show()

    def render_scroller(self, text, font, amplitude = 0, startpos = None):
        if not startpos:
            startpos = self.display.width
        scroller = Scroller(text, startpos, font, self.display, amplitude)
        timer = time.time() + self.duration
        while self.config.allow_screen_render(self.name):
            self.display.prepare()
            scroller.render()
            self.display.show()

            if scroller.pos == 2:
                self.capture_screenshot()

            if not self.config.allow_screen_render(self.name) or not scroller.move_for_next_frame(time.time() < timer):
                break

    def run(self):
        self.logger.info("'" + self.__class__.__name__ + "' rendering")
        self.display.prepare()
        self.render()
        self.logger.info("'" + self.__class__.__name__ + "' completed")

class StaticScreen(BaseScreen):
    @property
    def text(self):
        if not self._text:
            self.text = self.default_message
            self.logger.info("No static text found")

        if not self._text_compiled:
            self._text_compiled = True
            self._text = self.utils.compile_text(self._text)
            self.logger.info(f"Static screen text compiled: '{self._text}'")

        return self._text

    @text.setter
    def text(self, text):
        self._text = str(text)
        self._text_compiled = False
        self.logger.info(f"Static screen text: '{self._text}' added")

    @property
    def noscroll(self):
        if not hasattr(self, '_noscroll'):
            return False
        return self._noscroll

    @noscroll.setter
    def noscroll(self, state):
        self._noscroll = bool(state)
        self.logger.info(f"Static screens text animated set to '{str(self._noscroll)}'")

    # @property
    # def amplitude(self):
    #     if not self._amplitude:
    #         return 0
    #     return self._amplitude

    # @amplitude.setter
    # def amplitude(self, amplitude):
    #     self._amplitude = int(amplitude) * -1
    #     self.logger.info("Static screen amplitude: '" + str(self._amplitude) + "' set")

    def capture_screenshot(self):
        slug = Utils.slugify(self.text)
        super().capture_screenshot("static_" + slug)

    def render(self):
        self.display.prepare()
        font = self.font(size=16)
        text = self.text
        # amplitude = self.amplitude

        self.logger.info("Rendering static text: " + text)
        if not self.noscroll and Utils.requires_scroller(self.display, text, font):
            self.render_scroller(text, font)
        else:
            if not Utils.does_text_width_fit(self.display, text, font):
                self.logger.info("Static text too wide for screen")
                lines = textwrap.wrap(text, width=15)
                font = self.font(12)
                text_leading = 3
                y_text = self.display.height
                for i, line in enumerate(lines):
                    width, height = Utils.get_text_size(self.display, line, font)
                    new_y = y_text - height - (text_leading / 2)
                    if new_y > 0:
                        y_text = new_y
                    else:
                        y_text = 0
                        break

                y_text /= 2
                for line in lines:
                    width, height = Utils.get_text_size(self.display, line, font)
                    left = (self.display.width - width) / 2
                    self.display.draw.text((left, y_text), line, font=font, fill=255)
                    y_text += (height + text_leading)
            else:
                x, y = Utils.get_text_center(self.display, text, font)
                self.display.draw.text((x, y), self.text, font=font, fill=255)

            self.render_with_defaults()

class WelcomeScreen(BaseScreen):
    @property
    def text(self):
        if not self._text:
            self.text = self.default_message
            self.logger.info("No configured welcome text found")

        if not self._text_compiled:
            self._text_compiled = True
            self._text = self.utils.compile_text(self._text)
            self.logger.info("Welcome screen text compiled: '" + self._text + "'")

        return self._text

    @text.setter
    def text(self, text):
        self._text = str(text)
        self._text_compiled = False
        self.logger.info("Welcome screen text: '" + self._text + "' added")

    def render(self):
        '''
        Animated welcome screen
        Scrolls 'Welcome [hostname]' across the screen
        '''
        height = self.display.height
        font = self.font(size=16)
        self.render_scroller(self.text, font)

class SplashScreen(BaseScreen):
    img = Image.open(r"" + Utils.current_dir + "/img/home-assistant-logo.png")

    def __init__(self, duration, display = Display(), utils = Utils(), config = None):
        super().__init__(duration, display, utils, config)

    def render(self):
        '''
            Home Assistant screen. 
            If you're not using Home Assistant OS, disable this screen in the config
        '''
        os_info = self.utils.hassos_get_info('os/info')
        os_version = os_info['data']['version']
        os_upgrade = os_info['data']['update_available']  

        if (os_upgrade == True):
            os_version = os_version + "*"

        core_info = self.utils.hassos_get_info('core/info')
        core_version = core_info['data']['version']  
        core_upgrade = os_info['data']['update_available']
        if (core_upgrade == True):
            core_version =  core_version + "*"

        img_size = 26
        padding = 10
        textbox_x = img_size + padding

        # Get HA Logo and Resize
        logo = self.img.resize([img_size, img_size])
        logo = ImageOps.invert(logo)  

        # Merge HA Logo with Canvas.
        self.display.image.paste(logo,(-2,3))
        self.display.draw.line([(textbox_x, 16),(123,16)], fill=255, width=1)

        ln1 = self.utils.get_hostname()
        ln1_font = self.font(size=9, is_bold=True)
        self.display.draw.text((textbox_x, 2), ln1, font=ln1_font, fill=255)

        # Write Test, Eventually will get from HA API.
        ln2 = 'OS '+ os_version + ' - ' + core_version
        ln2_font = self.font()
        self.display.draw.text((textbox_x, 20), ln2, font=ln2_font, fill=255)

        self.render_with_defaults()

class NetworkScreen(BaseScreen):
    def render(self):
        self.hint = 'NET'
        self.set_icon('/img/ip-network.png')

        hostname = self.utils.get_hostname()
        ipv4 = self.utils.get_ip()

        self.display_text([ hostname, ipv4 ])
        #self.display_text([ hostname, ipv4, mac.upper() ])

        self.render_with_defaults()

class StorageScreen(BaseScreen):
    def render(self):
        self.hint = 'DSK'
        self.set_icon('/img/harddisk.png')
        drive = '/'

        #storage = Utils.shell_cmd('df -h | awk \'$NF=="/"{printf "%d,%d,%s", $3,$2,$5}\'')
        storage = Utils.shell_cmd('df ' + drive + ' | awk \'$NF=="/"{printf "%d,%d,%s", $3,$2,$5,$6}\'')
        storage = storage.split(',')

        used = int(storage[0]) / (1024 * 1024)
        total = int(storage[1]) / (1024 * 1024)
        free = total - used
        free_pct = 100 * (free / total)

        indent = self.text_indent
        if self.display.compact:
           self.display_text([ f"{round(used,1):.1f} / {round(total,0):.0f} GB",
                               f"{free_pct:.1f}% Free" ])
        else:
           self.display_text([
             f"USED: {round(used,1):.1f} GB",
             f"TOTAL: {round(total,1):.1f} GB",
             f"UTILISED: {storage[2]}" ])

        self.render_with_defaults()

class MemoryScreen(BaseScreen):
    def render(self):
        self.hint = 'MEM'
        self.set_icon("/img/memory.png")

        mem = Utils.shell_cmd("free -m | awk 'NR==2{printf \"%.1f,%.1f,%.0f%%\", $3/1000,$2/1000,$3*100/$2 }'")
        mem = mem.split(',')

        used = float(mem[0])
        total = float(mem[1])
        free_pct = 100 * (total - used) / total

        indent = self.text_indent
        if self.display.compact:
           self.display_text([ f"{round(used,1):.1f} / {round(total,1):.1f} GB",
                               f"{free_pct:.1f}% Free" ])
        else:
           self.display_text([
             f"USED: {used} GB",
             f"TOTAL: {total} GB",
             f"UTILISED: {mem[2]}" ])

        self.render_with_defaults()

class CpuScreen(BaseScreen):
    def set_temp_unit(self, unit):
        unit = str(unit).upper()
        if unit in ['C', 'F']:
            self.temp_unit = unit

    def get_temp(self):
        temp = float(Utils.shell_cmd("cat /sys/class/thermal/thermal_zone0/temp")) / 1000.00
        if (hasattr(self, 'temp_unit') and self.temp_unit == 'F'):
            temp = "%0.1f °F" % (temp * 9.0 / 5.0 + 32)
        else:
            temp = "%0.1f °C" % (temp)
        return temp

    def render(self):
        self.hint = 'CPU'
        self.set_icon("/img/cpu.png") 

        # switched from top -bn1 to uptime to reduce CPU consumption by 60%
        cpu = Utils.shell_cmd("uptime | grep -i load | awk '{printf \"%.2f,%.2f,%.2f\", $(NF-2),$(NF-1),$(NF)}'")
        cpu = cpu.split(',')

        uptime = Utils.shell_cmd("uptime | grep -ohe 'up .*' | sed 's/,//g' | awk '{ print $2" "$3 }'")

        # Check temperature unit and convert if required.
        temp = self.get_temp()

        indent = self.text_indent
        if self.display.compact:
           self.display_text([ f"{temp}",
                               f"{cpu[0]} {cpu[1]}" ])
        else:
           self.display_text([ f"TEMP: {temp}",
                               f"LOAD: {cpu[0]}",
                               uptime.upper() ])

        self.render_with_defaults()

