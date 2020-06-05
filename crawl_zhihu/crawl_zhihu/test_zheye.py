from zheye import zheye
z = zheye()
positions = z.Recognize('C:/Users/86151/Desktop/crawl_project/crawl_zhihu/crawl_zhihu/captcha .gif')
for i in positions:
    x = i[1]
    y = i[0]