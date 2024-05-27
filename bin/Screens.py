from PIL import Image, ImageDraw, ImageFont, ImageOps
import time
import logging
import textwrap
from bin.SSD1306 import SSD1306_128_32 as SSD1306
from bin.Scroller import Scroller
from bin.Utils import Utils
class Display:
    DEFAULT_BUSNUM = 1
    SCREENSHOT_PATH = "./img/examples/"

    def __init__(self, busnum = None, screenshot = False, rotate = False):
        if not isinstance(busnum, int):
            busnum = Display.DEFAULT_BUSNUM

        self.display = SSD1306(busnum)
        self.clear()
        self.width = self.display.width
        self.height = self.display.height
        self.rotate = rotate
        self.image = Image.new("1", (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)
        self.screenshot = screenshot
        self.logger = logging.getLogger('Display')

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
    font_path = Utils.current_dir + "/fonts/DejaVuSansMono.ttf"
    font_bold_path = Utils.current_dir + "/fonts/DejaVuSansMono-Bold.ttf"
    fonts = {}

    def __init__(self, duration, display = Display(), utils = Utils(), config = None):
        self.display = display
        self.duration = duration
        self.utils = utils
        self.config = config
        self.logger = logging.getLogger('Screen')
        self.logger.info("'" + self.__class__.__name__ + "' created")

    @property
    def name(self):
        return str(self.__class__.__name__).lower().replace("screen", "")

    def capture_screenshot(self, name = None):
        if not name:
            name = self.name
        self.display.capture_screenshot(name)

    def font(self, size, is_bold = False):
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
            self.logger.info("Static screen text compiled: '" + self._text + "'")

        return self._text

    @text.setter
    def text(self, text):
        self._text = str(text)
        self._text_compiled = False
        self.logger.info("Static screen text: '" + self._text + "' added")

    @property
    def noscroll(self):
        if not hasattr(self, '_noscroll'):
            return False
        return self._noscroll

    @noscroll.setter
    def noscroll(self, state):
        self._noscroll = bool(state)
        self.logger.info("Static screens text animated has been set to '" + str(self._noscroll) + "'")

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
        font = self.font(16)
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

            self.display.show()
            self.capture_screenshot()
            time.sleep(self.duration)

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
        font = self.font(16)
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
        ln1_font = self.font(9, True)
        self.display.draw.text((textbox_x, 2), ln1, font=ln1_font, fill=255)

        # Write Test, Eventually will get from HA API.
        ln2 = 'OS '+ os_version + ' - ' + core_version
        ln2_font = self.font(8)
        self.display.draw.text((textbox_x, 20), ln2, font=ln2_font, fill=255)

        # Display Image to OLED
        self.capture_screenshot()

        self.display.show()
        time.sleep(self.duration)

class NetworkScreen(BaseScreen):
    img = Image.open(r"" + Utils.current_dir + "/img/ip-network.png")

    def render(self):
        hostname = self.utils.get_hostname()
        ipv4 = self.utils.get_ip()

        # Resize and merge icon to Canvas
        icon = self.img.resize([13,13])
        self.display.image.paste(icon,(-2,0))

        self.display.draw.text((18, 0), hostname, font=self.font(12), fill=255)
        self.display.draw.text((0, 18), "IP4 " + ipv4, font=self.font(12), fill=255)    
        #draw.text((29, 21), "MAC " + mac.upper(), font=small, fill=255)    

        self.capture_screenshot()
        self.display.show()

        time.sleep(self.duration)

class StorageScreen(BaseScreen):
    img = Image.open(r"" + Utils.current_dir + "/img/harddisk.png") 

    def render(self):
        storage =  Utils.shell_cmd('df -h | awk \'$NF=="/"{printf "%d,%d,%s", $3,$2,$5}\'')
        storage = storage.split(',')

        # Resize and merge icon to Canvas
        icon = self.img.resize([26,26])  
        self.display.image.paste(icon,(-2,3))

        self.display.draw.text((29, 0), "USED: " + storage[0] + ' GB \n', font=self.font(8), fill=255)
        self.display.draw.text((29, 11), "TOTAL: " + storage[1] + ' GB \n', font=self.font(8), fill=255)
        self.display.draw.text((29, 21), "UTILISED: " + storage[2] + ' \n', font=self.font(8), fill=255) 

        self.capture_screenshot()
        self.display.show()
        time.sleep(self.duration)

class MemoryScreen(BaseScreen):
    img = Image.open(r"" + Utils.current_dir + "/img/database.png")

    def render(self):
        mem = Utils.shell_cmd("free -m | awk 'NR==2{printf \"%.1f,%.1f,%.0f%%\", $3/1000,$2/1000,$3*100/$2 }'")
        mem = mem.split(',')

        # Resize and merge icon to Canvas
        icon = self.img.resize([26,26])  
        self.display.image.paste(icon,(-2,3))

        self.display.draw.text((29, 0), "USED: " + mem[0] + ' GB \n', font=self.font(8), fill=255)
        self.display.draw.text((29, 11), "TOTAL: " + mem[1] + ' GB \n', font=self.font(8), fill=255)
        self.display.draw.text((29, 21), "UTILISED: " + mem[2] + ' \n', font=self.font(8), fill=255)  

        self.capture_screenshot()
        self.display.show()
        time.sleep(self.duration)

class CpuScreen(BaseScreen):
    img = Image.open(r"" + Utils.current_dir + "/img/cpu-64-bit.png") 

    def set_temp_unit(self, unit):
        unit = str(unit).upper()
        if unit in ['C', 'F']:
            self.temp_unit = unit

    def get_temp(self):
        temp =  float(Utils.shell_cmd("cat /sys/class/thermal/thermal_zone0/temp")) / 1000.00

        if (hasattr(self, 'temp_unit') and self.temp_unit == 'F'):
            temp = "%0.2f °F " % (temp * 9.0 / 5.0 + 32)
        else:
            temp = "%0.2f °C " % (temp)

        return temp

    def render(self):
        cpu = Utils.shell_cmd("top -bn1 | grep Load | awk '{printf \"%.2f\", $(NF-2)}'")
        uptime = Utils.shell_cmd("uptime | grep -ohe 'up .*' | sed 's/,//g' | awk '{ print $2" "$3 }'")

        # Check temapture unit and convert if required.
        temp = self.get_temp()

        # Resize and merge icon to Canvas
        icon = self.img.resize([26,26])  
        self.display.image.paste(icon,(-2,3))

        self.display.draw.text((29, 0), 'TEMP: ' + temp, font=self.font(8), fill=255)
        self.display.draw.text((29, 11), 'LOAD: '+ cpu + "% ", font=self.font(8), fill=255)  
        self.display.draw.text((29, 21), uptime.upper(), font=self.font(8), fill=255)

        self.capture_screenshot()
        
        self.display.show()
        time.sleep(self.duration)
class SummaryScreen(BaseScreen):
    @property
    def text(self):
        if not self._text:
            self.text = self.default_message
            self.logger.info("No summary text found")

        if not self._text_compiled:
            self._text_compiled = True
            self._text = self.utils.compile_text(self._text)
            self.logger.info("Summary screen text compiled: '" + self._text + "'")

        return self._text

    @text.setter
    def text(self, text):
        self._text = str(text)
        self._text_compiled = False
        self.logger.info("Summary screen text: '" + self._text + "' added")

    @property
    def noscroll(self):
        if not hasattr(self, '_noscroll'):
            return False
        return self._noscroll

    @noscroll.setter
    def noscroll(self, state):
        self._noscroll = bool(state)
        self.logger.info("Summary screens text animated has been set to '" + str(self._noscroll) + "'")

    def capture_screenshot(self):
        slug = Utils.slugify(self.text)
        super().capture_screenshot("summary_" + slug)

    def render(self):
        padding = -2
        height = self.display.height
        width = self.display.width
        top = padding
        bottom = height - padding
        x=0
        hostname = self.utils.get_hostname()
        ipv4 = self.utils.get_ip()
        uptime_in_seconds = self.utils.shell_cmd("cat /proc/uptime | cut -d' ' -f1")

        self.display.prepare()
        big_font = self.font(20)
        small_font = self.font(10)
        text = self.text

        self.logger.info("Rendering summary text: " + text)
        self.display.draw.text( (0, -2), hostname.lower(), font=big_font, fill=255)

        self.display.draw.text((x, top + 24), ipv4, font=small_font, fill=255)
        self.display.draw.text((width - 35 , top + 24), self.utils.display_time(float(uptime_in_seconds.strip()), 4), font=small_font, fill=255)


        self.display.show()
        self.capture_screenshot()
        time.sleep(self.duration)

