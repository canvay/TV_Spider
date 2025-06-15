# -*- coding:utf-8 -*-
import time
from urllib.parse import quote_plus
import requests
from bs4 import BeautifulSoup
import ddddocr
import urllib3
import re
import base64
import zlib


urllib3.util.timeout.Timeout._validate_timeout = lambda *args: 5 if args[2] != 'total' else None


Tag = "vodjp"
Tag_name = "荐片电影网"
siteUrl = "https://vodjp.com"


def getHeaders():
    headers = {}
    headers.setdefault("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0")
    return headers


def add_domain(matched):
    url = "https://vod.bdys.me/" + matched.group(0)
    return url

def Regex(pattern, content):
    try:
        matcher = re.findall(pattern, content)
        if matcher:
            return matcher[0]
    except Exception as e:
        print(e)
    return ""

def cacu(code):
    if "=" in code:
        code = code[:code.find("=")]
    elif code[-1] == "2" or code[-1] == "7":
        code = code[:-1]
        if code[-1] == "4" or code[-1] == "-":
            code = code[:-1]
    code = code.replace("I", "1")
    code = code.replace("l", "1")
    if code.isdigit():
        if len(code) > 4:
            code = code[:4]
        return int(code[:2]) - int(code[2:])
    elif "+" in code:
        code = code.split("+")
        return int(code[0]) + int(code[1])
    elif "-" in code:
        code = code.split("-")
        return int(code[0]) - int(code[1])
    elif "x" in code:
        code = code.split("x")
        return int(code[0]) * int(code[1])

def searchContent(key, token):
    try:
        url = siteUrl + "/jpsearch/-------------.html?wd=" + quote_plus(key)
        print(url)
        jS = BeautifulSoup(requests.get(url=url, headers=getHeaders()).text, "html.parser")
        videos = []
        lists = jS.select(".stui-vodlist > .stui-vodlist__item")
        for vod in lists:
            name = vod.h4.a.get_text().strip()
            if key in name:
                remarkspan = vod.select_one(".pic-text")
                vod_remarks = ""
                if remarkspan:
                    vod_remarks = Tag_name + " " + remarkspan.get_text()
                videos.append({
                    "vod_id": f'{Tag}${vod.a["href"].split("/")[-1].split(".")[0]}',
                    "vod_name": name,
                    "vod_pic": vod.a["data-original"],
                    "vod_remarks": vod_remarks
                })
        return videos
    except Exception as e:
        print(e)
    return []


def detailContent(ids, token):
    try:
        id = ids.split("$")[-1]
        url = f"{siteUrl}/jpvod/{id}.html"
        jS = BeautifulSoup(requests.get(url=url, headers=getHeaders()).text, "html.parser")
        # 取基本数据
        thumbdiv = jS.select_one(".stui-content__thumb")
        detaildiv = jS.select_one(".stui-content__detail")
        module_info_items = detaildiv.select(".data span")
        director = ""
        actor = ""
        type_name = ""
        vod_year = ""
        vod_area = ""
        vod_remarks = thumbdiv.a.span.get_text()
        for item in module_info_items:
            if "导演" in item.get_text():
                director = item.next_sibling
            elif "主演" in item.get_text():
                actor = item.next_sibling
            elif "类型" in item.get_text():
                type_name = item.next_sibling.get_text()
            elif "年份" in item.get_text():
                vod_year = item.next_sibling.strip()
            elif "地区" in item.get_text():
                vod_area = item.next_sibling.strip()
        vodList = {
            "vod_id": f'{Tag}${id}',
            "vod_name": detaildiv.h3.get_text(),
            "vod_pic": thumbdiv.a.img["data-original"],
            "type_name": type_name,
            "vod_year": vod_year,
            "vod_area": vod_area,
            "vod_remarks": vod_remarks,
            "vod_actor": actor,
            "vod_director": director,
            "vod_content": detaildiv.select_one(".desc").get_text().replace("简介：", "").strip(),
            "vod_play_from": "荐片电影网"
        }
        vod_play = {}
        # 取播放列表数据
        sources = jS.select(".stui-content__playlist > li")
        if len(sources) == 0:
            print("当前没有可播放的内容")
            return []
        vodItems = []
        for source in sources:
            sourceName = source.a.get_text()
            playURL = Regex("/jpplay/(.*)\\.html", source.a["href"])
            if not playURL:
                continue
            vodItems.append(sourceName + "$" + f"{Tag}___" + playURL)
        if len(vodItems):
            playList = "#".join(vodItems)
        vodList.setdefault("vod_play_url", playList)
        return [vodList]
    except Exception as e:
        print(e)
    return []


def playerContent(ids, flag, token):
    try:
        ids = ids.split("___")
        url = ids[-1]
        text = requests.get(url=f"{siteUrl}/jpplay/{url}.html", headers=getHeaders()).text
        m3u8_url = re.findall(r"https:[A-Za-z0-9_ ./\\]*\.m3u8", text)[0].replace("\\", "")
        m3u8_url_text = requests.get(url=m3u8_url, headers=getHeaders()).text
        pattern = r'^.+\.m3u8'

        match = re.search(pattern, m3u8_url_text, re.MULTILINE)
        if match:
            m3u8_url = m3u8_url.replace("index.m3u8", match.group())

        m3u8_content = requests.get(m3u8_url).text
        print(m3u8_content)
        # 将M3U8内容编码为Bytes
        m3u8_bytes = m3u8_content.encode('utf-8')
        # 将Bytes编码为Base64
        m3u8_base64 = base64.b64encode(m3u8_bytes).decode('utf-8')
        # 构造Data URI
        data_uri = f'data:application/vnd.apple.mpegurl;base64,{m3u8_base64}'
        return {
            "header": "",
            "parse": "0",
            "playUrl": "",
            "url": data_uri
        }
    except Exception as e:
        print(e)
    return {}


if __name__ == '__main__':
    res = searchContent("灰影人", "")
    # res = detailContent('bdys_old$/jingsong/22401', "")
    # res = detailContent('bdys_old$/meiju/21647', "")
    # func = "playerContent"
    # res = playerContent("bdys_old___/play/22401-0__1", "", "")
    # res = eval(func)("68614-1-1")
    print(res)
