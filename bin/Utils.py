import subprocess
import json
import pathlib
import re
class Utils:
    current_dir = str(pathlib.Path(__file__).parent.parent.resolve())

    @staticmethod
    def shell_cmd(cmd):
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode("utf-8")

    @staticmethod
    def get_text_center(display, text, font):
        w, h = Utils.get_text_size(display, text, font)
        calculated_width = (display.width - w) / 2
        calculated_height = (display.height - h) / 4
        return [calculated_width, calculated_height]

    @staticmethod
    def get_text_size(display, text, font):
        left, top, right, bottom = display.draw.textbbox((0, 0), text, font=font)
        width = right - left
        height = top - bottom
        return [width, height]

    @staticmethod
    def requires_scroller(display, text, font):
        w, unused = Utils.get_text_size(display, text, font)
        return display.width < w

    @staticmethod
    def get_hostname(opt = ""):
        return Utils.shell_cmd("hostname " + opt + "| cut -d\' \' -f1")

    @staticmethod
    def get_ip():
        return Utils.get_hostname('-I')



    @staticmethod
    def slugify(text):
        maxlength = 15
        slug = re.sub(r'[^a-z0-9\_ ]+', '', text.lower().strip()).replace(" ", "_")[0:maxlength].strip('_')
        return slug
        
class HassioUtils(Utils):
    @staticmethod
    def hassos_get_info(type):
        cmd = 'curl -sSL -H "Authorization: Bearer $SUPERVISOR_TOKEN" -H "Content-Type: application/json" http://supervisor/{}'.format(type)
        info = Utils.shell_cmd(cmd)
        return json.loads(info)

    @staticmethod
    def get_hostname(opt = ""):
        host_info = HassioUtils.hassos_get_info('host/info')
        return host_info['data']['hostname'].upper()

    @staticmethod
    def get_ip():
        network_info = HassioUtils.hassos_get_info('network/info')
        return network_info['data']['interfaces'][0]['ipv4']['address'][0].split("/")[0]