import os
import time
import random
import re
import textwrap
import requests
import yaml
from urllib import parse
from pyaes import AESModeOfOperationCBC
from requests import Session as req_Session


class HostlocGetPoints():

    tg_text = ''
    
    def __init__(self, config):
        self.config = config  # 从配置文件中加载的配置

    # 随机生成用户空间链接
    def randomly_gen_uspace_url(self) -> list:
        url_list = []
        for i in range(13):
            uid = random.randint(10000, 50000)
            url = 'https://hostloc.com/space-uid-{}.html'.format(str(uid))
            url_list.append(url)
        return url_list

    def toNumbers(self, secret: str) -> list:
        text = []
        for value in textwrap.wrap(secret, 2):
            text.append(int(value, 16))
        return text

    def check_anti_cc(self) -> dict:
        result_dict = {}
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'
        }
        home_page = 'https://hostloc.com/forum.php'
        try:
            res = requests.get(home_page, headers=headers)
            res.raise_for_status()
            aes_keys = re.findall('toNumbers\("(.*?)"\)', res.text)
            cookie_name = re.findall('cookie="(.*?)="', res.text)

            if len(aes_keys) != 0:
                print('检测到防 CC 机制开启！')
                if len(aes_keys) != 3 or len(cookie_name) != 1:
                    result_dict['ok'] = 0
                else:
                    result_dict['ok'] = 1
                    result_dict['cookie_name'] = cookie_name[0]
                    result_dict['a'] = aes_keys[0]
                    result_dict['b'] = aes_keys[1]
                    result_dict['c'] = aes_keys[2]
        except requests.exceptions.RequestException as e:
            print(f"请求失败: {e}")
        return result_dict

    def gen_anti_cc_cookies(self) -> dict:
        cookies = {}
        anti_cc_status = self.check_anti_cc()

        if anti_cc_status:
            if anti_cc_status['ok'] == 0:
                print('防 CC 验证过程所需参数不符合要求，页面可能存在错误！')
            else:
                print('自动模拟计算尝试通过防 CC 验证')
                a = bytes(self.toNumbers(anti_cc_status['a']))
                b = bytes(self.toNumbers(anti_cc_status['b']))
                c = bytes(self.toNumbers(anti_cc_status['c']))
                cbc_mode = AESModeOfOperationCBC(a, b)
                result = cbc_mode.decrypt(c)

                name = anti_cc_status['cookie_name']
                cookies[name] = result.hex()
        return cookies

    def login(self, username: str, password: str) -> req_Session:
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
            'origin': 'https://hostloc.com',
            'referer': 'https://hostloc.com/forum.php',
        }
        login_url = 'https://hostloc.com/member.php?mod=logging&action=login&loginsubmit=yes&infloat=yes&lssubmit=yes&inajax=1'
        login_data = {
            'fastloginfield': 'username',
            'username': username,
            'password': password,
            'quickforward': 'yes',
            'handlekey': 'ls',
        }

        s = req_Session()
        s.headers.update(headers)
        s.cookies.update(self.gen_anti_cc_cookies())

        retries = 0
        while retries < self.config['max_retries']:
            try:
                res = s.post(url=login_url, data=login_data)
                res.raise_for_status()
                print(f"登录成功: {username}")
                return s
            except requests.exceptions.RequestException as e:
                print(f"登录失败，第{retries + 1}次重试: {e}")
                retries += 1
                time.sleep(self.config['retry_delay'])  # 重试前等待

        print(f"登录失败，达到最大重试次数 {self.config['max_retries']} 次")
        return None

    def check_login_status(self, s: req_Session, number_c: int) -> bool:
        test_url = 'https://hostloc.com/home.php?mod=spacecp'
        try:
            res = s.get(test_url)
            res.raise_for_status()
            res.encoding = 'utf-8'
            test_title = re.findall("<title>(.*?)<\/title>", res.text)

            if len(test_title) != 0 and test_title[0] != '个人资料 -  全球主机交流论坛 -  Powered by Discuz!':
                print(f'第{number_c}个帐户登录失败！')
                self.tg_text = self.tg_text + '\n第{}个帐户登录失败！\n'.format(number_c)
                return False
            else:
                print(f'第{number_c}个帐户登录成功！')
                self.tg_text = self.tg_text + '\n第{}个帐户登录成功！\n'.format(number_c)
                return True
        except requests.exceptions.RequestException as e:
            print(f"检查登录状态失败: {e}")
            return False

    def print_current_points(self, s: req_Session):
        test_url = 'https://hostloc.com/forum.php'
        try:
            res = s.get(test_url)
            res.raise_for_status()
            res.encoding = 'utf-8'
            points = re.findall("积分: (\d+)", res.text)

            if points:
                print(f'帐户当前积分：{points[0]}')
                self.tg_text = self.tg_text + '帐户当前积分：' + points[0] + '\n'
            else:
                print('无法获取帐户积分，可能页面存在错误或者未登录！')
                self.tg_text = self.tg_text + '无法获取帐户积分，可能页面存在错误或者未登录！' + '\n'
        except requests.exceptions.RequestException as e:
            print(f"获取积分失败: {e}")

    def get_points(self, s: req_Session, number_c: int):
        if self.check_login_status(s, number_c):
            self.print_current_points(s)
            url_list = self.randomly_gen_uspace_url()
            success, fail = 0, 0
            for i, url in enumerate(url_list):
                try:
                    res = s.get(url)
                    res.raise_for_status()
                    print(f'第{i + 1}个用户空间链接访问成功')
                    success += 1
                    time.sleep(5)
                except requests.exceptions.RequestException as e:
                    fail += 1
                    print(f'链接访问异常：{e}')
            self.tg_text += f'用户空间成功访问{success}个，访问失败{fail}个\n'
            self.print_current_points(s)
        else:
            print('请检查你的帐户是否正确！')
            self.tg_text += '请检查你的帐户是否正确！\n'

    def post(self, bot_api, chat_id, text):
        print('开始推送')
        headers = {
            'user-agent': 'Mozilla/5.0 (Linux; Android 6
