# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import datetime

from MySQLdb.cursors import DictCursor
from twisted.enterprise import adbapi


class CrawlZhihuPipeline:
    def __init__(self,dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_settings(cls,settings):
        """获取settings配置的数据库信息"""
        dbparms = dict(
            host=settings['MYSQL_HOST'],
            db=settings['MYSQL_DB'],
            user=settings['MYSQL_USER'],
            passwd=settings['MYSQL_PASSWD'],
            charset='utf8mb4',
            cursorclass=DictCursor,
            use_unicode=True
        )
        # 使用MySQLdb这个库 第二个参数为连接mysql基本配置
        dbpool = adbapi.ConnectionPool("MySQLdb", **dbparms)
        # 这里会return到 __init__里面去
        return cls(dbpool)

    def process_item(self, item, spider):
        # 运行的程序,就如同多线程的run 第一个参数为调用方法名,第二个为传进去的参数
        query = self.dbpool.runInteraction(self.insert_mysql, item)
        # 处理异常的方法
        query.addErrback(self.handle_err, item, spider)
        return item

    def insert_mysql(self,cursor,item):
        """插入数据库"""
        insert_mysql = """
            insert into zhihu_questions(id,question_title,question_content,question_url,crawl_time)
            VALUES (%s,%s,%s,%s,%s) on DUPLICATE KEY UPDATE 
            question_title=VALUES(question_title),
            question_url=VALUES (question_url),
            question_content=values (question_content)
            
        """

        mysql_list = []
        mysql_list.append(item.get('id', ""))  # 主键id
        mysql_list.append(item.get('question_title', ""))  # 标题
        mysql_list.append(item.get('question_content', ""))  # 富文本内容
        mysql_list.append(item.get('question_url', ""))  # 从哪里来
        mysql_list.append(datetime.datetime.now())  # 创建时间
        cursor.execute(insert_mysql, mysql_list)

        insert_mysql = """
            insert into zhihu_answer(answer_author,answer_content,answer_created_time,crawl_time,zhihu_questions_id)
            VALUES (%s,%s,%s,%s,%s) on DUPLICATE KEY UPDATE
            answer_author=VALUES(answer_author),
            answer_content=VALUES (answer_content),
            answer_created_time=values (answer_created_time),
            crawl_time=values (crawl_time),
            zhihu_questions_id=values (zhihu_questions_id)
        """
        #用户回答列表
        answer_list = item.get("answer_list")
        for data in answer_list:
            mysql_list = []
            mysql_list.append(data.get('answer_author', ""))  # 作者名称
            mysql_list.append(data.get('answer_content', ""))  # 富文本内容
            mysql_list.append(data.get('answer_created_time', ""))  # 回答时间
            mysql_list.append(datetime.datetime.now())  # 创建时间
            mysql_list.append(data.get('id', ""))  # 外键id
            cursor.execute(insert_mysql, mysql_list)


    def handle_err(self,failure,item,spider):
        """处理异常"""
        print(failure)
        print(item)
        print(item)


