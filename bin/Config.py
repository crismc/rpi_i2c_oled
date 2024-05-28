import logging
import json
import signal

from bin.Screens import *
from bin.Scroller import Scroller
from bin.Utils import HassioUtils, Utils


class Config:
    DEFAULT_DURATION = 10
    SUPPORTED_SCREENS = [
        'welcome',
        'splash',
        'network',
        'storage',
        'memory',
        'cpu',
        'static'
    ]
    HASSIO_DEPENDENT_SCREENS = [
        'Splash'
    ]
    OPTION_KEYS = {
        'show': 'show_{}_screen',
        'limit': '{}_screen_limit',
        'duration': '{}_screen_duration',
        'temp_unit': 'temperature_unit',
        'default_duration': 'default_duration',
        'i2c_bus': 'i2c_bus',
        'screenshot': 'screenshot',
        'graceful_exit_text': 'graceful_exit_text',
        'static_screen_text': 'static_screen_text',
        'static_screen_text_noscroll': 'static_screen_text_noscroll',
        'scroll_amplitude': 'scroll_amplitude',
        'datetime_format': 'datetime_format',
        'welcome_screen_text': 'welcome_screen_text',
        'rotate': 'rotate',
        'show_icons': 'show_icons',
        'show_hint': 'show_hint',
        'compact': 'compact'
    }

    logger = logging.getLogger('Config')

    def __init__(self, path):
        self._load_options(path)
        self.default_duration = Config.DEFAULT_DURATION
        self._process_default_options()
        self.enabled_screens = []
        self.screen_limits = {}

    def _load_options(self, path):
        Config.logger.info('Loading config: ' + path)
        f = open(path, "r")
        options = json.loads(f.read())
        self.options = {k.lower(): v for k, v in options.items()}

    def _process_default_options(self):
        duration = self.get_option_value('default_duration')
        if duration:
            self.default_duration = int(duration)

        scroller_amplitude = self.get_option_value('scroll_amplitude')
        if scroller_amplitude:
            Scroller.default_amplitude = scroller_amplitude

    def allow_screen_render(self, screen):
        if self.allow_master_render:
            if screen in self.screen_limits:
                if self.screen_limits[screen]:
                    return True
                else:
                    return False

            return True

        Config.logger.info('Master renderer killed... kill, kill, kill it with a knife')
        return False

    @property
    def allow_master_render(self):
        if hasattr(self, 'graceful_exit'):
            return not self.graceful_exit.exit

        return True

    @property
    def is_hassio_supported(self):
        if hasattr(Config, 'hassio_supported'):
            return Config.hassio_supported

        try:
            info = HassioUtils.hassos_get_info('host/info')
            if info:
                Config.hassio_supported = True
                Config.logger.info('Home Assistant instance found')
            else:
                Config.hassio_supported = False
                Config.logger.info('Home Assistant is not supported on this instance')
        except:
            Config.hassio_supported = False
            Config.logger.info('Home Assistant is not supported on this instance')

        return Config.hassio_supported

    def _init_display(self):
        try:
            busnum = None
            if self.has_option('i2c_bus'):
                busnum = int(self.get_option_value('i2c_bus'))

            screenshot = self.get_option_value('screenshot')
            if not screenshot:
                screenshot = False

            rotate = self.get_option_value('rotate')
            show_icons = self.get_option_value('show_icons')
            show_hint = self.get_option_value('show_hint')
            compact = self.get_option_value('compact')

            self.display = Display(busnum=busnum, screenshot=screenshot,
                                   rotate=rotate, show_icons=show_icons,
                                   show_hint=show_hint, compact=compact)

        except Exception as e:
            raise Exception("Could not create display. Check your i2c bus with 'ls /dev/i2c-*'.")

    def _init_utils(self):
        if self.is_hassio_supported:
            self.utils = HassioUtils
        else:
            self.utils = Utils

        datetime_format = self.get_option_value('datetime_format')
        if datetime_format:
            self.utils.datetime_format = datetime_format

    def enable_screen(self, name):
        if name in Config.SUPPORTED_SCREENS and name not in self.enabled_screens:
            if name not in Config.HASSIO_DEPENDENT_SCREENS or self.is_hassio_supported:
                self.enabled_screens.append(name.lower())

    def remove_enabled_screen(self, name):
        if name in self.enabled_screens:
            self.enabled_screens.remove(name)
            Config.logger.info("'" + name + "' removed from enabled screens")

    def add_screen_limit(self, screen, limit):
        Config.logger.info("'" + screen + "' limited to " + str(limit) + " iterations")
        self.screen_limits[screen.lower()] = int(limit)

    def reduce_screen_limit(self, screen):
        screen = screen.lower()
        if screen in self.screen_limits:
            self.screen_limits[screen] = self.screen_limits[screen] - 1
            Config.logger.info("'" + screen + "' limit reduced to " + str(self.screen_limits[screen]) + " iterations")
            if not self.screen_limits[screen]:
                Config.logger.info("'" + screen + "' iteration limit reached")
                self.remove_enabled_screen(screen)

    def get_enabled_screens(self):
        '''
            Get a list of screens which have been configured by checking the 'show_[name]_screen' option
            If the property is not present, assume True
        '''
        for screen in Config.SUPPORTED_SCREENS:
            if self.has_option('show', screen):
                if self.get_option_value('show', screen):
                    self.enable_screen(screen)
                    limit = self.get_option_value('limit', screen)
                    if limit:
                        self.add_screen_limit(screen, limit)
            else:
                self.enable_screen(screen)

        return self.enabled_screens

    def add_option(self, key, value):
        id = str(key.lower())
        if id in Config.OPTION_KEYS:
            self.options[key] = value
            Config.logger.info("'" + str(value) + "' added to the '" + key + "' config")
        return False

    def has_option(self, key, screen = None):
        id = str(key.lower())

        if id in Config.OPTION_KEYS:
            if screen:
                key = Config.OPTION_KEYS[id].format(str(screen).lower())
            else:
                key = Config.OPTION_KEYS[id]
                
            if key in self.options.keys():
                return key
        
        return False

    def get_option_value(self, key, screen = None):
        key = self.has_option(key, screen)
        if key:
            return self.options[key]

    def get_screen_duration(self, name):
        if name in self.enabled_screens:
            duration = self.get_option_value('duration', name)
            if not duration:
                duration = self.default_duration

            return int(duration)

    def screen_factory(self, name):
        name = str(name).lower()

        if not hasattr(self, 'display'):
            self._init_display()

        if not hasattr(self, 'utils'):
            self._init_utils()

        if name == 'static':
            duration = self.get_screen_duration(name)
            screen = StaticScreen(duration, self.display, self.utils, self)
            static_text = self.get_option_value('static_screen_text')
            if static_text:
                screen.text = static_text
                if self.get_option_value('static_screen_text_noscroll'):
                    screen.noscroll = True
            return screen
        elif name in self.enabled_screens:
            class_name = name.capitalize() + 'Screen'
            duration = self.get_screen_duration(name)
            screen = globals()[class_name](duration, self.display, self.utils, self)

            if name == 'cpu':
                screen.set_temp_unit(self.get_option_value('temp_unit'))

            if name == 'welcome':
                screen.text = self.get_option_value('welcome_screen_text')
                screen.amplitude = self.get_option_value('scroll_amplitude')
            return screen
        else:
            raise Exception(name + " is not an enabled screen")

    def enable_graceful_exit(self):
        screen = self.screen_factory('static')
        text = self.get_option_value('graceful_exit_text')
        if not text:
            text = 'Goodbye'
        
        screen.text = text
        screen.duration = 0
        screen.noscroll = True

        self.graceful_exit = GracefulExit(screen)
        Config.logger.info('Graceful exit enabled')

class GracefulExit:
    exit = False
    exiting = False
    def __init__(self, screen):
        self.screen = screen
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, *args):
        self.exit = True
        if not self.exiting:
            self.exiting = True
            Config.logger.info('Exiting')
            # self.screen.display.clear()
            # self.screen.display.prepare()
            # self.screen.display.show()
            self.screen.run()
