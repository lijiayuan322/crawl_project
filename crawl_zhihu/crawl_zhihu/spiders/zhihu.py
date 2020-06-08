# -*- coding: utf-8 -*-
import base64
import json
import os
import re
import time
from urllib import parse

import mouse
import scrapy
from selenium import webdriver
from PIL import Image
from selenium.webdriver.common.keys import Keys

from crawl_zhihu import constant
from crawl_zhihu.items import CrawlZhihuItem
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
                        #报错,暂时注销
                        # browser.find_element_by_xpath(
                        #     "//label[@class=‘Input-wrapper’]/input[@name=‘captcha’]").send_keys(Keys.CONTROL + 'a')
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


            except Exception as f:
                print(f)
                print(f)

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
        # with open('C:/Users/86151/Desktop/crawl_project/crawl_zhihu/cookies.json', 'r') as f:
        #     cookies_dict=json.loads(f.read())

        yield scrapy.Request(url=self.start_urls[0], dont_filter=True, cookies=cookies_dict,callback=self.parse)

    def parse(self, response):
            #获取网页所有url

        url_all = response.xpath("//a/@href").extract()
        p = re.compile(r'.*?/(question/(\d+))/?.*')
        # 列获取url 和 url_id
        url_list = [dict(url= parse.urljoin('https://www.zhihu.com',p.match(url).group(1)),
                    id= p.match(url).group(2)) for url in url_all if p.match(url) ]
        for url_dict in url_list:
            yield scrapy.Request(url=url_dict['url'],callback=self.handle_url)

        #处理下拉刷新的url
        url_refresh_start = "https://www.zhihu.com/api/v3/feed/topstory/recommend?session_token=e51ed9eb5bc6cb44e8146256bf5d8631&desktop=true&page_number=2&limit=6&action=down&after_id=5&ad_interval=-1"
        yield scrapy.Request(url=url_refresh_start,callback=self.handle_refresh)

    def handle_refresh(self,response):
        """首页刷新加载出来的url"""
        return_dict = json.loads(response.text)
        paging = return_dict.get("paging")
        #获取url
        data_list = return_dict.get("data")
        if data_list:
            for data in data_list:
                target = data.get("target")
                if target:
                    question = target.get("question")
                    if question:
                        id = question.get('id')
                        type = question.get('type')
                        if type == "question":
                            #yield  https://www.zhihu.com/question/(\d+)
                            yield scrapy.Request(url=parse.urljoin('https://www.zhihu.com/',str(type) + "/"+ str(id) ),callback=self.handle_url)

        if paging.get("is_end",True) == False:
            #表示不是尾页
            next_page_url = paging.get('next')
            #yield 下一页链接
            yield scrapy.Request(url=next_page_url,callback=self.handle_refresh)
        #不符合以上条件直接return掉
        return

    def handle_url(self,response):
        """处理url   question/number"""
        # HTML返回的response为残缺HTML
        question_title = response.xpath("//title").extract_first()
        #匹配url末尾数字正则
        p_id = '.*?/question/(\d+)'

        id = re.search(p_id,response.url).group(1)
        #HTML返还的文本
        text = response.text
        #把所有需要转码的匹配出来
        p = re.compile("\\\\u[0-9]{3}[A-Z]")
        result_list = p.findall(text)
        #提出出来的 \uxxx 去重
        result_set = set(result_list)
        for code in result_set:
            #转码
            code_after = code.encode('utf-8').decode('unicode_escape')
            #替换转码
            text = text.replace(code,code_after)
        # content正则
        p_content = '"commentPermission":"all","detail":"(.*?)(","editableDetail").*?,"status":'
        question_content = re.search(p_content, text)
        if question_content:
            question_content = question_content.group(1)
        else:
            p_content = '"commentPermission":"all","detail":"(.*?)","status":'
            question_content = re.search(p_content, text)
            if question_content:
                question_content = question_content.group(1)
            else:
                question_content = ""

        print(question_content)
        print(question_content)

        answer_url_start = "https://www.zhihu.com/api/v4/questions/{}/answers?include=data%5B%2A%5D.is_normal%2Cadmin_closed_comment%2Creward_info%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_reason%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Ccreated_time%2Cupdated_time%2Creview_info%2Crelevant_info%2Cquestion%2Cexcerpt%2Crelationship.is_authorized%2Cis_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cis_labeled%2Cis_recognized%2Cpaid_info%2Cpaid_info_content%3Bdata%5B%2A%5D.mark_infos%5B%2A%5D.url%3Bdata%5B%2A%5D.author.follower_count%2Cbadge%5B%2A%5D.topics&limit=5&offset=0&platform=desktop&sort_by=default".format(id)
        yield scrapy.Request(url=answer_url_start,callback=self.handle_answer_url,meta={"question_title":question_title,
                                                                                        "question_content":question_content,
                                                                                        "id":id,
                                                                                        "question_url":response.url}
                                )

    def handle_answer_url(self,response):
        """处理回答url"""
        #实例化item
        crawlzhihuitem = CrawlZhihuItem()
        answer_dict = json.loads(response.text)

        crawlzhihuitem["question_title"] = response.meta.get("question_title","")
        crawlzhihuitem["question_content"] = response.meta.get("question_content","")
        crawlzhihuitem["id"] = response.meta.get("id","")
        crawlzhihuitem["question_url"] = response.meta.get("question_url","")
        #是否最后一页
        is_end = answer_dict.get("paging").get("is_end")
        #下一页url
        next_url = answer_dict.get("paging").get("next")
        if not is_end and next_url:
            yield scrapy.Request(url=next_url,callback=self.handle_answer_url)
        #answer数据列表
        data_list = answer_dict.get("data")
        #用户回答信息
        answer_info = []
        for data in data_list:
            #获取创建时间
            try:
                time_result = time.localtime(data.get('created_time'))
                time_result = time.strftime("%Y-%m-%d %H:%M:%S", time_result)
            except:
                time_result = ""
            #获取作者名称
            try:
                answer_author = data.get("author").get("name")
            except:
                answer_author = ""
            #获取用户回答内容
            answer_content = data.get("content")
            #保存字典形式
            answer_dict = dict(
                id = response.meta.get("id",""),
                answer_created_time = time_result,
                answer_author = answer_author,
                answer_content = answer_content
            )
            #将字典信息保存到列表中
            answer_info.append(answer_dict)
        crawlzhihuitem['answer_list'] = answer_info
        if crawlzhihuitem['id'] == "":
            return
        yield crawlzhihuitem











