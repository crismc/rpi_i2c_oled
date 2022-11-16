import sys
import getopt
import os
import logging
from bin.Config import Config
from bin.Utils import Utils

def print_help():
    filename = os.path.basename(__file__)
    print (filename + ' -c <config_path>')
    print (filename + ' --config <config_path>')

def start(config, logger):
    screens = config.get_enabled_screens()
    
    if not screens:
        raise Exception("No screens are available")

    while config.allow_master_render:
        for name in screens:
            logger.info("'" + name + "' is being processed")
            if config.allow_render(name):
                try:
                    screen = config.screen_factory(name)
                    screen.run()
                    config.reduce_screen_limit(name)
                except Exception as e:
                    logger.critical("Screen '" + name + "' has an internal error: " + str(e))
                    continue

def set_logging_level(level):
    logging.basicConfig()
    main = logging.getLogger(__name__)
    screen = logging.getLogger('Screen')
    config = logging.getLogger('Config')

    if level:
        main.setLevel(level)
        screen.setLevel(level)
        config.setLevel(level)

    return main;

if __name__ == "__main__":
    args = sys.argv[1:]
    config_path = Utils.current_dir + '/options.json'

    logger = set_logging_level(logging.INFO)

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
        config = Config(config_path)

    start(config, logger)