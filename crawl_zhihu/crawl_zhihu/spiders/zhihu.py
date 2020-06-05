# -*- coding: utf-8 -*-
import base64
import json
import os
import time

import mouse
import scrapy
from selenium import webdriver
from PIL import Image
from selenium.webdriver.common.keys import Keys

from crawl_zhihu import constant
from crawl_zhihu.ttshitu_english_verify import base64_api


class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com/']

    def start_requests(self):
        """重写start_url"""

        # 浏览器驱动
        path = os.path.join(os.path.dirname(os.path.abspath(os.path.dirname(os.path.abspath(__file__)))),
                            'chromedriver_win32', 'chromedriver.exe')
        # chrome浏览器
        browser = webdriver.Chrome(executable_path=path)
        # 最大化
        browser.maximize_window()
        # 访问链接
        browser.get(self.start_urls[0])
        try:
            # 点击一下密码登录跳转密码登录界面,报错的话证明已登录
            browser.find_element_by_xpath("//div[@class='SignFlow-tab']").click()
            time.sleep(3)
            # 输入用户密码
            browser.find_element_by_xpath("//label[@class='SignFlow-accountInput Input-wrapper']/input").send_keys(
                constant.ZHIHU_USER)
            browser.find_element_by_xpath("//label/input[@name='password']").send_keys(constant.ZHIHU_PSWD)
            # 点击登录
            browser.find_element_by_xpath("//form/button").click()
            try:
                # 选取密码登录xpath,如果已经登录则报错
                browser.find_element_by_xpath(
                    "//form[@class='SignFlow Login-content']/div/div[@class='SignFlow-tab']")
                # ===============================================================================
                # 验证码类型 None为无 chineseImg为中文验证码  englishImg为英文验证码
                verify = None
                # 图片element
                img = None
                # Captcha - englishImg
                try:
                    # 使用xpath定位英文验证码图片,如果报错则不是英文验证码
                    img = browser.find_element_by_xpath("//img[@class='Captcha-englishImg']")
                    verify = 'englishImg'
                except:
                    pass
                # Captcha-chineseImg
                try:
                    # 使用xpath定位中文验证码图片,如果报错则不是中文验证码
                    img = browser.find_element_by_xpath("//img[@class='Captcha-chineseImg']")
                    verify = 'chineseImg'
                except:
                    pass
                    # =================================================================================

                # 验证码图片位置
                verify_img = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                    'verify_img.jpeg')

                # 获取浏览器上面地址栏的高度
                browser_navigation_panel_height = browser.execute_script(
                    'return window.outerHeight - window.innerHeight;')
                while True:

                    if img is not None:
                        time.sleep(3)
                        img_src = img.get_attribute('src').replace("data:image/jpg;base64,", "")
                        # 获取验证码的x,y坐标
                        coordinate_x = img.location['x']
                        coordinate_y = img.location['y']


                        with open('verify_img.jpeg', 'wb') as f:
                            f.write(base64.b64decode(img_src))
                    # 重复执行登录操作,直到登录成功
                    if verify == 'chineseImg':
                        # 中文验证码
                        # github  zheye 的倒立文字验证码
                        from zheye import zheye
                        z = zheye()
                        positions = z.Recognize(verify_img)
                        # positions返还一个list 里面是一个个元组 (y,x)
                        if len(positions) > 0:
                            for i in positions:
                                x = i[1]
                                y = i[0]

                                # 坐标需要扣除browser_navigation_panel_height的高度
                                move_y = browser_navigation_panel_height + coordinate_y + y / 2
                                move_x = x / 2 + coordinate_x
                                mouse.move(move_x, move_y)
                                time.sleep(2)
                                mouse.click()

                    if verify == 'englishImg':
                        img = Image.open(verify_img)
                        result = base64_api(uname=constant.TTST_USER, pwd=constant.TTST_PSWD, img=img)
                        # # 输入英文验证码结果
                        # browser.find_element_by_xpath(
                        #     "//label[@class='Input-wrapper']/input[@name='captcha']").send_keys(Keys.CONTROL + "a")
                        time.sleep(2)
                        #输入英文验证码结果
                        browser.find_element_by_xpath(
                            "//label[@class='Input-wrapper']/input[@name='captcha']").send_keys(result)
                    time.sleep(1)
                    # 点击登录
                    browser.find_element_by_xpath("//form/button").click()
                    time.sleep(2)

                    try:
                        # 选取密码登录xpath,如果已经登录找不到则报错
                        name = browser.find_element_by_xpath(
                            "//form[@class='SignFlow Login-content']/div/div[@class='SignFlow-tab']")
                    except:
                        break


            except:
                pass

        except:
            pass
        #获取网页cookies
        chooies = browser.get_cookies()
        #以 name:value的形式保存cookies
        cookies_dict = {}
        for i in chooies:
            cookies_dict[i['name']] = i['value']
        json.dump(cookies_dict, open('cookies.json', "w"))
        cookies_dict = json.load(open('cookies.json'))
        browser.close()
        yield scrapy.Request(url=self.start_urls[0], dont_filter=True, cookies=cookies_dict,callback=self.parse)


    def parse(self, response):
            print(123)
