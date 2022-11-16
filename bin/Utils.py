import subprocess
import json
import pathlib

class Utils:
    current_dir = str(pathlib.Path(__file__).parent.parent.resolve())

    @staticmethod
    def shell_cmd(cmd):
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode("utf-8")

    @staticmethod
    def get_text_center(display, text, font, center_point):
        w, h = display.draw.textsize(text, font=font)
        return (center_point - (w / 2))

    @staticmethod
    def get_hostname(opt = ""):
        return Utils.shell_cmd("hostname " + opt + "| cut -d\' \' -f1")

    @staticmethod
    def get_ip():
        return Utils.get_hostname('-I')
        
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