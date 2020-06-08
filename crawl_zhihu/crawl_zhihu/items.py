# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class CrawlZhihuItem(scrapy.Item):
    # #回答内容
    # answer_content = scrapy.Field()
    # #回答创建时间
    # answer_created_time = scrapy.Field()
    # #回答问题的作者
    # answer_author = scrapy.Field()
    answer_list = scrapy.Field()

    id = scrapy.Field()

    #问题标题
    question_title = scrapy.Field()
    #问题内容
    question_content = scrapy.Field()
    #url
    question_url = scrapy.Field()


