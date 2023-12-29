import subprocess
import json
import pathlib
import re
import logging
from datetime import datetime
class Utils:
    logger = logging.getLogger('Utils')
    current_dir = str(pathlib.Path(__file__).parent.parent.resolve())

    @staticmethod
    def shell_cmd(cmd):
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode("utf-8")

    @staticmethod
    def get_text_center(display, text, font):
        w, h = Utils.get_text_size(display, text, font)
        left = (display.width - w) / 2
        top = (display.height - h) / 2
        return [left, top]

    @staticmethod
    def get_text_size(display, text, font):
        left, top, right, bottom = display.draw.textbbox((0, 0), text, font=font)
        width = right - left if left > right else right - left
        height = top - bottom if bottom < top else bottom - top
        return [width, height]

    @staticmethod
    def requires_scroller(display, text, font):
        w, unused = Utils.get_text_size(display, text, font)
        return display.width < w

    @staticmethod
    def get_hostname(opt = ""):
        return str(Utils.shell_cmd("hostname " + opt + "| cut -d\' \' -f1")).strip()

    @staticmethod
    def get_ip():
        return Utils.get_hostname('-I')

    def get_datetime(format = None):
        if not format:
            format = Utils.datetime_format if hasattr(Utils, 'datetime_format') else "%d/%m/%Y %H:%M:%S"
        return datetime.now().strftime(format)

    @staticmethod
    def compile_text(text, additional_replacements = {}):
        replacements = {
            "{hostname}": lambda prop: Utils.get_hostname(),
            "{ip}": lambda prop: Utils.get_ip(),
            "{datetime}": lambda prop: Utils.get_datetime()
        }
        replacements = {**replacements, **additional_replacements}
        regex = re.compile("(%s)" % "|".join(map(re.escape, replacements.keys())))
        return regex.sub(lambda match: replacements[match.string[match.start():match.end()]](match.string[match.start():match.end()]), text)

    @staticmethod
    def does_text_width_fit(display, text, font):
        left, top, right, bottom = display.draw.textbbox((0, 0), text, font=font)
        return display.width > right - left

    @staticmethod
    def slugify(text):
        maxlength = 15
        slug = re.sub(r'[^a-z0-9\_ ]+', '', text.lower().strip()).replace(" ", "_")[0:maxlength].strip('_')
        return slug
        
class HassioUtils(Utils):
    @staticmethod
    def hassos_get_info(type):
        url = 'http://supervisor/{}'.format(type)
        Utils.logger.info("Requesting data from '" + url + "'")
        cmd = 'curl -sSL -H "Authorization: Bearer $SUPERVISOR_TOKEN" -H "Content-Type: application/json" ' + url
        info = Utils.shell_cmd(cmd)
        return json.loads(info)

    @staticmethod
    def get_hostname(opt = ""):
        host_info = HassioUtils.hassos_get_info('host/info')
        return host_info['data']['hostname'].upper()

    @staticmethod
    def get_ip():
        network_info = HassioUtils.hassos_get_info('network/info')
        first_interface_with_ipv4 = next((interface for interface in network_info["data"]["interfaces"] if interface["ipv4"]["address"]), None)
        if first_interface_with_ipv4:
            return first_interface_with_ipv4["ipv4"]["address"][0].split("/")[0]
        else:
            return "0.0.0.0"

    @staticmethod
    def compile_text(text, additional_replacements = {}):
        replacements = {
            "{hostname}": lambda prop: HassioUtils.get_hostname(),
            "{ip}": lambda prop: HassioUtils.get_ip()
        }
        text = Utils.compile_text(text, {**replacements, **additional_replacements})
        regex = re.compile("{hassio\.[a-z]+\.[a-z\.]+}")
        return regex.sub(lambda match: HassioUtils.get_hassio_info_property(match.string[match.start():match.end()][len("hassio\."):-1]), text)

    @staticmethod
    def get_hassio_info_property(properties_string):
        '''
            properties_string = namespace.rootproperty.leaf
            e.g. properties_string as 'os.version.latest' will find {'latest':'version'} in os/info
        '''
        properties = properties_string.split('.')
        namespace = properties[0]
        properties.pop(0)
        url = str(namespace) + "/info"
        Utils.logger.info("Searching '"+ namespace +" for': " + '.'.join(properties))
        try :
            info = HassioUtils.hassos_get_info(url)
            if info and 'data' in info:
                value = info['data']
                data_key = namespace
                for prop in properties:
                    if prop in value:
                        value = value[prop]
                        data_key = '.'.join([data_key, prop])
                    else:
                        raise Exception("Could not find '" + value + "' in '" + data_key + "'")

                if isinstance(value, dict):
                    raise Exception("'" + property + "' is not a leaf")

                return value
            else:
                raise Exception("No data available")
        except Exception as e:
            Utils.logger.warning("Could not load hassio info url '"+ url +"': " + str(e))
