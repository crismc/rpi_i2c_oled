import sys
import getopt
import os
import logging
from bin.Config import Config
from bin.Utils import Utils
from bin.Screens import Display

LOG_LEVEL = logging.WARNING

def print_help():
    filename = os.path.basename(__file__)
    print (filename + ' [OPTIONS]... -c <config_path>')
    print (' ')
    print ('-h, --help')
    print ('   Prints out this help information')
    print (' ')
    print ('-d, --debug')
    print ('   Enable debug mode, printing out the process steps to STDOUT. NOTE: This doesnt include i2c display debugging')
    print (' ')
    print ('-c <config_path>, --config <config_path>')
    print ('   JSON options file')
    print ('   example:')
    print ('     ' + filename + ' -c /path/to/options.json')
    print ('     ' + filename + ' --config /path/to/options.json')
    print (' ')
    print ('-s <optional_save_path>, --screenshot <optional_save_path>')
    print ('   Save a screenshot to the specified location. If no path is specified, .png files are saved to ' + Display.SCREENSHOT_PATH)
    print ('   example:')
    print ('     ' + filename + ' -s')
    print ('     ' + filename + ' --screenshot')
    print ('     ' + filename + ' -s /path/to/image/store')
    print ('     ' + filename + ' --screenshot /path/to/image/store')

def start(config, logger):
    screens = config.get_enabled_screens()
    
    if not screens:
        raise Exception("No screens are available")

    config.enable_graceful_exit()

    while config.allow_master_render:
        for name in screens:
            if config.allow_screen_render(name):
                logger.info("'" + name + "' is being processed")
                try:
                    screen = config.screen_factory(name)
                    logger.info("Setuping up factory")
                    screen.run()
                    config.reduce_screen_limit(name)
                except Exception as e:
                    logger.critical("Screen '" + name + "' has an internal error: " + str(e))
                    continue

def set_logging_level(level):
    logging.basicConfig(format='[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
                        datefmt='%m-%d %H:%M:%S')
    main = logging.getLogger(__name__)
    if level: main.setLevel(level)
    for name in ['Screen', 'Config', 'Display', 'Utils']:
        log = logging.getLogger(name)
        if level: log.setLevel(level)

    return main;

if __name__ == "__main__":
    args = sys.argv[1:]
    config_path = Utils.current_dir + '/options.json'
    screenshot = False

    try:
        opts, args = getopt.getopt(args,"hdss:c:",["config=", "help", "debug", "screenshot=", "screenshot"])
    except getopt.GetoptError:
        print_help()
        sys.exit(2)
 
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print_help()
            sys.exit()
        elif opt in ("-c", "--config"):
            config_path = arg
        elif opt in ("-d", "--debug"):
            LOG_LEVEL = logging.INFO
        elif opt in ("-s", "--screenshot"):
            if arg:
                screenshot = arg
            else:
                screenshot = True

    logger = set_logging_level(LOG_LEVEL)

    if config_path:
        try:
            config = Config(config_path)
            if screenshot:
                config.add_option('screenshot', screenshot)
        except Exception as e:
            print(str(e))
            sys.exit(2)
    else:
        logger.critical("No options.json file available.")
        sys.exit(2)

    start(config, logger)
