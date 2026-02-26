import requests
from bs4 import BeautifulSoup
import smtplib
import ssl
from email.mime.text import MIMEText
import os

# ========= 标题判断 =========

VALID_WORDS = ["招聘", "公开招聘", "事业单位", "人才引进", "招录"]
INVALID_WORDS = ["会议", "解读", "政策解读", "公示结果"]

# ========= 结构生物学技能关键词 =========

STRUCTURE_SKILLS = [
    # 蛋白相关
    "蛋白表达", "蛋白纯化", "重组蛋白", "层析", "AKTA",

    # 结构解析
    "晶体", "蛋白晶体", "晶体学",
    "X射线", "X射线衍射",
    "冷冻电镜", "cryo-EM", "cryoEM",
    "cryo-FIB", "FIB",
    "电镜", "透射电镜", "扫描电镜",

    # 数据分析
    "结构解析", "单颗粒分析", "亚断层平均",
    "结构生物学",

    # 平台相关
    "电镜平台", "大型仪器", "仪器管理",
    "共享平台", "公共技术平台"
]

# ========= 岗位类型关键词 =========

POSITION_KEYWORDS = [
    "平台主管",
    "平台工程师",
    "结构生物学平台",
    "仪器平台主管",
    "技术支撑",
    "专技岗位",
    "实验技术",
    "工程师",
    "科研助理"
]

# ========= 单位类型关键词 =========

INSTITUTION_KEYWORDS = [
    "大学",
    "医学院",
    "生命科学学院",
    "结构生物中心",
    "科研院所",
    "中国科学院",
    "重点实验室",
    "公共平台",
    "共享实验室"
]

# ========= 监控入口 =========

URLS = {
    "广东人社": "http://hrss.gd.gov.cn/gkmlpt/index",
    "湖南人社": "http://rst.hunan.gov.cn/rst/xxgk/zpzl/",
    "重庆人社": "http://rlsbj.cq.gov.cn/zwxx_182/sydw/",
    "浙江人社": "http://rlsbt.zj.gov.cn/col/col1229743683/index.html",
    "上海人社": "https://rsj.sh.gov.cn/trsrc_177/",
}

EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER")

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# ========= 邮件发送 =========

def send_email(content):
    msg = MIMEText(content, "plain", "utf-8")
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg["Subject"] = "【结构生物学岗位监控提醒】"

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL("smtp.qq.com", 465, context=context) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())

# ========= 标题过滤 =========

def title_valid(title):
    if len(title) < 6:
        return False
    if any(b in title for b in INVALID_WORDS):
        return False
    if any(v in title for v in VALID_WORDS):
        return True
    return False

# ========= 核心匹配逻辑（只要匹配任意一个关键词就推送） =========

def content_matches(text, title):

    all_keywords = STRUCTURE_SKILLS + POSITION_KEYWORDS + INSTITUTION_KEYWORDS

    # 正文匹配
    if any(word in text for word in all_keywords):
        return True

    # 标题匹配
    if any(word in title for word in all_keywords):
        return True

    return False

# ========= 主函数 =========

def fetch_jobs():
    results = []

    for region, url in URLS.items():
        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            response.encoding = "utf-8"
            soup = BeautifulSoup(response.text, "lxml")

            for link in soup.find_all("a"):
                title = link.get_text().strip()

                if not title_valid(title):
                    continue

                job_url = link.get("href")
                if not job_url:
                    continue

                if not job_url.startswith("http"):
                    job_url = requests.compat.urljoin(url, job_url)

                try:
                    detail = requests.get(job_url, headers=HEADERS, timeout=15)
                    detail.encoding = "utf-8"
                    text = detail.text

                    if content_matches(text, title):
                        results.append(f"{region} | {title}\n{job_url}\n")

                except:
                    continue

        except:
            continue

    if results:
        content = "\n\n".join(results)
        send_email(content)

if __name__ == "__main__":
    fetch_jobs()
