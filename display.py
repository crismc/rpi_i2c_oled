import math
import time
import subprocess
import json
import pathlib
import sys
import getopt
import os

from PIL import Image, ImageDraw, ImageFont, ImageOps

import SSD1306

## Global Variables
# Default set, but can be overridden by config in addon setup.
TEMP_UNIT = "C"

IS_HASIO = False
SCREENSHOT_CAPTURE = False

SCREEN_SPLASH = 'Splash_Screen'
SCREEN_CPU = 'CPU_Screen'
SCREEN_NETWORK = 'Network_Screen'
SCREEN_MEMORY = 'Memory_Screen'
SCREEN_STORAGE = 'Storage_Screen'
SCREEN_WELCOME = 'Welcome_Screen'

SCREEN_OPT_SHOW = 'Show'
SCREEN_OPT_LIMIT = 'Limit'
SCREEN_OPT_DURATION = 'Duration'
SCREEN_OPT_LIMITREMAINING = 'LIMIT_REMAINING'
SCREEN_OPT_RENDERER = 'RENDERER'

SCREENS = {
    SCREEN_WELCOME: {
        SCREEN_OPT_SHOW: True,
        SCREEN_OPT_RENDERER: "render_welcome"
    },
    SCREEN_SPLASH: {
        SCREEN_OPT_SHOW: False,
        SCREEN_OPT_RENDERER: "render_splash"
    },
    SCREEN_NETWORK: {
        SCREEN_OPT_SHOW: True,
        SCREEN_OPT_RENDERER: "render_network",
    },
    SCREEN_CPU: {
        SCREEN_OPT_SHOW: True,
        SCREEN_OPT_RENDERER: "render_cpu_temp"
    },
    SCREEN_MEMORY: {
        SCREEN_OPT_SHOW: True,
        SCREEN_OPT_RENDERER: "render_memory"
    },
    SCREEN_STORAGE: {
        SCREEN_OPT_SHOW: True,
        SCREEN_OPT_RENDERER: "render_storage"
    }
}

DEFAULT_DURATION = 10

# Create the SSD1306 OLED class.
I2C_BUS = 1
disp = SSD1306.SSD1306_128_32(I2C_BUS)
current_dir = str(pathlib.Path(__file__).parent.resolve())

# Clear display.
disp.begin()
disp.clear()
disp.display()

# Create blank image for drawing.
width = disp.width
height = disp.height

image = Image.new("1", (width, height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Load default font.
# font = ImageFont.load_default()
p = ImageFont.truetype(current_dir + "/fonts/DejaVuSans.ttf", 9)
p_bold = ImageFont.truetype(current_dir + "/fonts/DejaVuSans-Bold.ttf", 9)
small = ImageFont.truetype(current_dir + "/fonts/DejaVuSans.ttf", 8)
smaller = ImageFont.truetype(current_dir + "/fonts/DejaVuSans.ttf", 7)
medium = ImageFont.truetype(current_dir + "/fonts/DejaVuSans.ttf", 12)
large = ImageFont.truetype(current_dir + "/fonts/DejaVuSans.ttf", 16)

img_network = Image.open(r"" + current_dir + "/img/ip-network.png") 
img_mem = Image.open(r"" + current_dir + "/img/database.png") 
img_disk = Image.open(r"" + current_dir + "/img/harddisk.png") 
img_ha_logo = m = Image.open(r"" + current_dir + "/img/home-assistant-logo.png") 
img_cpu_64 = Image.open(r"" + current_dir + "/img/cpu-64-bit.png") 

run_main_loop = True
home_assistant = None

def start():
    while run_main_loop:
        for name, config in SCREENS.items():
            if run_main_loop and show_screen(name):
                func_to_run = globals()[config[SCREEN_OPT_RENDERER]]
                func_to_run(config)

def capture_screenshot(name):
    if SCREENSHOT_CAPTURE:
        image.save(r"./img/examples/" + name + ".png")

def render_storage(config):
    storage =  shell_cmd('df -h | awk \'$NF=="/"{printf "%d,%d,%s", $3,$2,$5}\'')
    storage = storage.split(',')

    # Clear Canvas
    draw.rectangle((0,0,128,32), outline=0, fill=0)

    # Resize and merge icon to Canvas
    icon = img_disk.resize([26,26])  
    image.paste(icon,(-2,3))

    draw.text((29, 0), "USED: " + storage[0] + ' GB \n', font=small, fill=255)
    draw.text((29, 11), "TOTAL: " + storage[1] + ' GB \n', font=small, fill=255)
    draw.text((29, 21), "UTILISED: " + storage[2] + ' \n', font=small, fill=255) 

    capture_screenshot("storage")

    disp.image(image)
    disp.display()
    time.sleep(get_duration(SCREEN_STORAGE))  

def render_memory(config):
    mem = shell_cmd("free -m | awk 'NR==2{printf \"%.1f,%.1f,%.0f%%\", $3/1000,$2/1000,$3*100/$2 }'")
    mem = mem.split(',')

    # Clear Canvas
    draw.rectangle((0,0,128,32), outline=0, fill=0)

    # Resize and merge icon to Canvas
    icon = img_mem.resize([26,26])  
    image.paste(icon,(-2,3))

    draw.text((29, 0), "USED: " + mem[0] + ' GB \n', font=small, fill=255)
    draw.text((29, 11), "TOTAL: " + mem[1] + ' GB \n', font=small, fill=255)
    draw.text((29, 21), "UTILISED: " + mem[2] + ' \n', font=small, fill=255)  

    capture_screenshot("memory")

    disp.image(image)
    disp.display()
    time.sleep(get_duration(SCREEN_MEMORY)) 

def render_cpu_temp(config):
    #host_info = hassos_get_info('host/info')
    cpu = shell_cmd("top -bn1 | grep load | awk '{printf \"%.2f\", $(NF-2)}'")
    temp =  float(shell_cmd("cat /sys/class/thermal/thermal_zone0/temp")) / 1000.00
    uptime = shell_cmd("uptime | grep -ohe 'up .*' | sed 's/,//g' | awk '{ print $2" "$3 }'")

    # Check temapture unit and convert if required.
    if (TEMP_UNIT == 'C'): 
        temp = "%0.2f °C " % (temp)
    else:
        temp = "%0.2f °F " % (temp * 9.0 / 5.0 + 32)


    # Clear Canvas
    draw.rectangle((0,0,128,32), outline=0, fill=0)

    # Resize and merge icon to Canvas
    icon = img_cpu_64.resize([26,26])  
    image.paste(icon,(-2,3))

    draw.text((29, 0), 'TEMP: ' + temp, font=small, fill=255)
    draw.text((29, 11), 'LOAD: '+ cpu + "% ", font=small, fill=255)  
    draw.text((29, 21), uptime.upper(), font=small, fill=255)

    capture_screenshot("cpu")
    
    disp.image(image)
    disp.display()
    time.sleep(get_duration(SCREEN_CPU))

def render_network(config):
    hostname = get_hostname()
    if IS_HASIO:
        network_info = hassos_get_info('network/info')
        ipv4 = network_info['data']['interfaces'][0]['ipv4']['address'][0].split("/")[0]
    else:
        ipv4 = get_hostname("-I")

    # Clear Canvas
    draw.rectangle((0,0,128,32), outline=0, fill=0)

    # Resize and merge icon to Canvas
    icon = img_network.resize([13,13])
    image.paste(icon,(-2,0))

    draw.text((18, 0), hostname, font=medium, fill=255)
    draw.text((0, 18), "IP4 " + ipv4, font=medium, fill=255)    
    #draw.text((29, 21), "MAC " + mac.upper(), font=small, fill=255)    

    capture_screenshot("network")

    disp.image(image)
    disp.display()
    time.sleep(get_duration(SCREEN_NETWORK))

def render_splash(config):
    '''
        Home Assistant screen. 
        If you're not using Home Assistant OS, disable this screen in the config
    '''
    if not IS_HASIO:
        return

    os_info = hassos_get_info('os/info')
    os_version = os_info['data']['version']
    os_upgrade = os_info['data']['update_available']  

    if (os_upgrade == True):
        os_version = os_version + "*"

    core_info = hassos_get_info('core/info')
    core_version = core_info['data']['version']  
    core_upgrade = os_info['data']['update_available']
    if (core_upgrade == True):
        core_version =  core_version + "*"

    # Draw a padded black filled box with style.border width.
    draw.rectangle((0, 0, width, height), outline=0, fill=0)

    # Get HA Logo and Resize
    logo = img_ha_logo.resize([26,26])
    logo = ImageOps.invert(logo)  
    
    # Merge HA Logo with Canvas.
    image.paste(logo,(-2,3))

    draw.line([(34, 16),(123,16)], fill=255, width=1)

    ln1 = "Home Assistant"
    ln1_x = get_text_center(ln1, p_bold, 78)
    draw.text((ln1_x, 2), ln1, font=p_bold, fill=255)

    # Write Test, Eventually will get from HA API.
    ln2 = 'OS '+ os_version + ' - ' + core_version
    ln2_x = get_text_center(ln2, small, 78)
    draw.text((ln2_x, 20), ln2, font=small, fill=255)

    # Display Image to OLED
    capture_screenshot("splash")
    disp.image(image)
    disp.display() 
    time.sleep(get_duration(SCREEN_SPLASH))

def render_welcome(config):
    '''
    Animated welcome screen
    Scrolls 'Welcome [hostname]' across the screen
    '''
    hostname = get_hostname()
    scroller = Scroller('Welcome to ' + hostname, height/2 - 8, width, height/4, large)
    timer = time.time() + get_duration(SCREEN_WELCOME)
    while True:
        draw.rectangle((0,0,width,height), outline=0, fill=0)
        scroller.render()
        disp.image(image)
        disp.display()
        
        if scroller.pos == 2:
            capture_screenshot("welcome")

        if not scroller.move_for_next_frame(time.time() < timer):
            break

def render_static(config):
    if 'text' in config.keys():
        text = config.text
    else:
        text = 'Welcome to ' + get_hostname()
    draw.rectangle((0,0,width,height), outline=0, fill=0)
    draw.text((3, 4), text, font=large, fill=255)
    disp.image(image)
    disp.display()

def get_text_center(text, font, center_point):
    w, h = draw.textsize(text, font=font)
    return (center_point -(w/2))

def hassos_get_info(type):
    cmd = 'curl -sSL -H "Authorization: Bearer $SUPERVISOR_TOKEN" -H "Content-Type: application/json" http://supervisor/{}'.format(type)
    info = shell_cmd(cmd)
    return json.loads(info)

def get_hostname(opt = ""):
    global IS_HASIO

    if IS_HASIO:
        host_info = hassos_get_info('host/info')
        hostname = host_info['data']['hostname'].upper()
    else:
        hostname = shell_cmd("hostname " + opt + "| cut -d\' \' -f1")

    return hostname

def shell_cmd(cmd):
    return subprocess.check_output(cmd, shell=True).decode("utf-8")

def get_duration(screen):
    if screen in SCREENS:
        config = SCREENS[screen]
        return config[SCREEN_OPT_DURATION] if SCREEN_OPT_DURATION in config else DEFAULT_DURATION
    return DEFAULT_DURATION

def show_screen(screen):
    if screen in SCREENS:
        if SCREENS[screen][SCREEN_OPT_SHOW]:
            if SCREEN_OPT_LIMIT in SCREENS[screen] and SCREENS[screen][SCREEN_OPT_LIMIT]:
                if SCREEN_OPT_LIMITREMAINING not in SCREENS[screen]:
                    SCREENS[screen][SCREEN_OPT_LIMITREMAINING] = SCREENS[screen][SCREEN_OPT_LIMIT]
                if SCREEN_OPT_LIMITREMAINING in SCREENS[screen]:
                    if SCREENS[screen][SCREEN_OPT_LIMITREMAINING]:
                        SCREENS[screen][SCREEN_OPT_LIMITREMAINING] = SCREENS[screen][SCREEN_OPT_LIMITREMAINING] - 1
                        return True
                    else:
                        return False
            
            return True
        else:
            return False

    print("Screen " + screen + " is not configured")
    return False

class Scroller:
    def __init__(self, text, offset = 12, startpos = width, amplitude = 0, font = large, velocity = -2, draw_obj = draw, width = width):
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

def get_options(config_path):
    f = open(config_path, "r")
    options = json.loads(f.read())
    global TEMP_UNIT, DEFAULT_DURATION, IS_HASIO

    TEMP_UNIT = options['Temperature_Unit']
    DEFAULT_DURATION = options['Default_Duration']

    if 'HASIO' in options:
        IS_HASIO = bool(options['HASIO'])
    else:
        IS_HASIO = True

    set_screen_options(SCREEN_WELCOME, options)
    set_screen_options(SCREEN_SPLASH, options)
    set_screen_options(SCREEN_NETWORK, options)
    set_screen_options(SCREEN_CPU, options)
    set_screen_options(SCREEN_MEMORY, options)
    set_screen_options(SCREEN_STORAGE, options)

def set_screen_options(screen, options):
    global SCREENS
    SCREENS[screen][SCREEN_OPT_SHOW] = options['Show_' + screen]
    if screen + '_Limit' in options and options[screen + '_Limit']:
        SCREENS[screen][SCREEN_OPT_LIMIT] = options[screen + '_Limit']
    if screen + '_Duration' in options and options[screen + '_Duration']:
        SCREENS[screen][SCREEN_OPT_DURATION] = options[screen + '_Duration']

def print_help():
    filename = os.path.basename('/root/file.ext')
    print (filename + ' -c <config_path>')
    print (filename + ' --config <config_path>')

if __name__ == "__main__":
    args = sys.argv[1:]
    config_path = current_dir + '/options.json'

    try:
        opts, args = getopt.getopt(args,"hc:",["config=", "help"])
    except getopt.GetoptError:
        print_help()
        sys.exit(2)
 
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print_help()
            sys.exit()
        elif opt in ("-c", "--config"):
            config_path = arg

    if config_path:
        get_options(config_path)

    start()