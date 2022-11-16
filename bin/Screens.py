from PIL import Image, ImageDraw, ImageFont, ImageOps
import time
import logging
from bin.SSD1306 import SSD1306_128_32 as SSD1306
from bin.Scroller import Scroller
from bin.Utils import Utils, HassioUtils

class Display:
    DEFAULT_BUSNUM = 1
    SCREENSHOT_PATH = "./img/examples/"

    def __init__(self, busnum = None, screenshot = False):
        if not isinstance(busnum, int):
            busnum = Display.DEFAULT_BUSNUM

        self.display = SSD1306(busnum)
        self.clear()
        self.width = self.display.width
        self.height = self.display.height
        self.image = Image.new("1", (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)
        self.screenshot = screenshot
        self.logger = logging.getLogger('Display')

    def clear(self):
        self.display.begin()
        self.display.clear()
        self.display.display()

    def prepare(self):
        self.draw.rectangle((0, 0, self.width, self.width), outline = 0, fill = 0)

    def show(self):
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
        self.logger = logging.getLogger('Screen')
        self.logger.info("'" + self.__class__.__name__ + "' created")

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

    def render(self):
        self.display.show()

    def run(self):
        self.logger.info("'" + self.__class__.__name__ + "' rendering")
        self.display.prepare()
        self.render()
        self.logger.info("'" + self.__class__.__name__ + "' completed")

class StaticScreen(BaseScreen):
    def render(self, text):
        self.display.prepare()
        font = self.font(16)
        x, y = Utils.get_text_center(self.display, text, font)
        self.display.draw.text((x, y), text, font=font, fill=255)
        self.display.show()
        slug = Utils.slugify(text)
        self.display.capture_screenshot("static_" + slug)

    def run(self, text):
        self.logger.info("'" + self.__class__.__name__ + "' rendering")
        self.display.clear()
        self.display.prepare()
        self.render(text)
        self.logger.info("'" + self.__class__.__name__ + "' completed")

class WelcomeScreen(BaseScreen):
    def render(self):
        '''
        Animated welcome screen
        Scrolls 'Welcome [hostname]' across the screen
        '''
        hostname = self.utils.get_hostname()
        height = self.display.height
        width = self.display.width
        font = self.font(16)
        message = 'Welcome to ' + hostname
        scroller = Scroller(message, width, height/6, font, self.display)
        timer = time.time() + self.duration

        while self.config.allow_screen_render('welcome'):
            self.display.prepare()
            scroller.render()
            self.display.show()
            
            if scroller.pos == 2:
                self.display.capture_screenshot("welcome")

            if not self.config.allow_screen_render('welcome') or not scroller.move_for_next_frame(time.time() < timer):
                break

class SplashScreen(BaseScreen):
    img = Image.open(r"" + Utils.current_dir + "/img/home-assistant-logo.png")

    def __init__(self, duration, font, display, utils):
        if not isinstance(utils, HassioUtils):
            return False

        super().__init__(duration, font, display, utils)

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

        # Get HA Logo and Resize
        logo = self.img.resize([26,26])
        logo = ImageOps.invert(logo)  
        
        # Merge HA Logo with Canvas.
        self.display.image.paste(logo,(-2,3))
        self.display.draw.line([(34, 16),(123,16)], fill=255, width=1)

        ln1 = "Home Assistant"
        ln1_font = self.font(9, True)
        ln1_x, ln1_y = Utils.get_text_center(self.display, ln1, ln1_font)
        self.display.draw.text((ln1_x, 2), ln1, font=ln1_font, fill=255)

        # Write Test, Eventually will get from HA API.
        ln2 = 'OS '+ os_version + ' - ' + core_version
        ln2_font = self.font(8)
        ln2_x, ln2_y = Utils.get_text_center(self.display, ln2, ln2_font)
        self.display.draw.text((ln2_x, 20), ln2, font=ln2_font, fill=255)

        # Display Image to OLED
        self.display.capture_screenshot("splash")

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

        self.display.capture_screenshot("network")
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

        self.display.capture_screenshot("storage")
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

        self.display.capture_screenshot("memory")
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
        cpu = Utils.shell_cmd("top -bn1 | grep load | awk '{printf \"%.2f\", $(NF-2)}'")
        uptime = Utils.shell_cmd("uptime | grep -ohe 'up .*' | sed 's/,//g' | awk '{ print $2" "$3 }'")

        # Check temapture unit and convert if required.
        temp = self.get_temp()

        # Resize and merge icon to Canvas
        icon = self.img.resize([26,26])  
        self.display.image.paste(icon,(-2,3))

        self.display.draw.text((29, 0), 'TEMP: ' + temp, font=self.font(8), fill=255)
        self.display.draw.text((29, 11), 'LOAD: '+ cpu + "% ", font=self.font(8), fill=255)  
        self.display.draw.text((29, 21), uptime.upper(), font=self.font(8), fill=255)

        self.display.capture_screenshot("cpu")
        
        self.display.show()
        time.sleep(self.duration)