"""天天视图验证码接口 http://www.ttshitu.com/"""

import json
import requests
import base64
from io import BytesIO
from PIL import Image
from sys import version_info

from crawl_zhihu import constant


def base64_api(uname, pwd,  img):
    img = img.convert('RGB')
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    if version_info.major >= 3:
        b64 = str(base64.b64encode(buffered.getvalue()), encoding='utf-8')
    else:
        b64 = str(base64.b64encode(buffered.getvalue()))
    data = {"username": uname, "password": pwd, "image": b64}
    result = json.loads(requests.post("http://api.ttshitu.com/base64", json=data).text)
    if result['success']:
        return result["data"]["result"]
    else:
        return result["message"]
    return ""


if __name__ == "__main__":
    img_path = "C:/Users/86151/Desktop/crawl_project/crawl_zhihu/verify_img.jpeg"
    img = Image.open(img_path)
    result = base64_api(uname=constant.TTST_USER, pwd=constant.TTST_PSWD, img=img)
    print(result)