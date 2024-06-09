import random
import re
import time
import os
import configparser
import requests
import xmltodict
from flask import Flask, request, jsonify

app = Flask(__name__)

WECHAT_API_URL = 'http://127.0.0.1:8888/api/'
config = configparser.ConfigParser()
config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
with open(config_path, 'r', encoding='utf-8') as f:
    config.read_file(f)
CURRENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))

IMAGE_DIRECTORY = os.path.join(CURRENT_DIRECTORY, "jpg")  # 图片文件目录
FILE_DIRECTORY = os.path.join(CURRENT_DIRECTORY, "file")  # 文件目录

jpgxml1 = "1.jpg"
filexml1 = "1.txt"

jpgxml = os.path.join(IMAGE_DIRECTORY, jpgxml1).replace("\\", "\\\\")
filexml = os.path.join(FILE_DIRECTORY, filexml1).replace("\\", "\\\\")

text_responses = {k: v for k, v in config.items('Responses')}
file_responses = {k: os.path.join(CURRENT_DIRECTORY, v.replace("/", os.sep)) for k, v in config.items('Files')}


@app.route('/wechatSDK', methods=['POST'])
def chat():
    data = request.json
    msg_type = data["data"]['type']
    msg_content = data["data"]["content"]
    send_channel = data["data"]["from"]

    if msg_type == 1:  # 文本消息
        return handle_text_msg(send_channel, msg_content)
    elif msg_type == 37:  # 被添加好友消息
        handle_add_friend_msg(data)
        return jsonify({"success": "true"})
    return jsonify({"error": "Unsupported message type"})


def handle_text_msg(send_channel, msg_content):
    if "@chatroom" in send_channel:
        return None

    # 检查消息内容是否包含文本消息关键词
    for keyword, response in text_responses.items():
        if keyword in msg_content:
            random_delay = random.randint(3, 12)
            time.sleep(random_delay)
            send_reply(send_channel, response)
            return jsonify({"success": "true"})

    # 检查消息内容是否包含文件消息关键词
    for keyword, file_path in file_responses.items():
        if keyword in msg_content:
            random_delay = random.randint(3, 12)
            time.sleep(random_delay)
            if file_path.endswith(".jpg"):
                send_image(send_channel, file_path)
            else:
                send_file(send_channel, file_path)
            return jsonify({"success": "true"})

    return jsonify({"success": "false", "message": "未找到匹配的关键字"})




def send_reply(to, content):
    payload = {
        "type": 10009,
        "userName": to,
        "msgContent": content,
        "insertToDatabase": False
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(WECHAT_API_URL, json=payload, headers=headers)
    if response.status_code == 200:
        print(f"消息已发送至{to}：{content}")
    else:
        print(f"无法将消息发送至 {to}：{content}")


def send_image(to, file_path):
    payload = {
        "type": 10010,
        "userName": to,
        "filePath": file_path
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(WECHAT_API_URL, json=payload, headers=headers)
    if response.status_code == 200:
        print(f"图片已发送至{to}：{file_path}")
    else:
        print(f"无法将图片发送至 {to}：{file_path}")


def send_file(to, file_path):
    payload = {
        "type": 10012,
        "userName": to,
        "filePath": file_path,
        "bAsync": False
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(WECHAT_API_URL, json=payload, headers=headers)
    if response.status_code == 200:
        print(f"文件已发送至{to}：{file_path}")
    else:
        print(f"无法将文件发送至 {to}：{file_path}")


def handle_add_friend_msg(data):
    xmlContent = data['data']['content']
    content = xmltodict.parse(xmlContent)
    username = content['msg']['@encryptusername']
    ticket = content['msg']['@ticket']
    randomTime = random.randint(3, 12)
    time.sleep(randomTime)
    response = requests.post(
        WECHAT_API_URL,
        json={
            "type": 10035,
            "encryptUserName": username,
            "ticket": ticket,
        })
    # 打印出返回的完整json数据
    response_data = response.json()
    print("response_data", response_data)

    if response_data['data']['status'] == 0:
        # 获取用户信息
        username = response_data['data']['userName']
        if username:
            user_info = get_user_info(username)
            if user_info:
                random_delay = random.randint(3, 12)
                time.sleep(random_delay)
                send_image(username, os.path.join(IMAGE_DIRECTORY, jpgxml))
                random_delay = random.randint(3, 12)
                time.sleep(random_delay)
                # 发送文件
                send_file(username, os.path.join(FILE_DIRECTORY, filexml))
            else:
                print(f"消息发送失败，无法获取用户信息")
        else:
            print(f"同意好友请求失败")
    pass


def get_user_info(username):
    payload = {
        "type": 10015,
        "userName": username
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(WECHAT_API_URL, json=payload, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if data['data']['status'] == 0:
            return data['data']['data']
    return None


def addCallBackUrl(callBackUrl):
    resdatalist = requests.post(WECHAT_API_URL, json={"type": 1003}).json()["data"]["data"]
    for item in resdatalist:
        requests.post(WECHAT_API_URL, json={"type": 1002, "cookie": item["cookie"]})
    requests.post(WECHAT_API_URL, json={"type": 1001, "protocol": 2, "url": callBackUrl})


if __name__ == '__main__':
    try:
        addCallBackUrl("http://127.0.0.1:18000/wechatSDK")
        print("连接微信成功")
    except Exception as e:
        print("连接微信失败", e)
    app.run(host='0.0.0.0', port=18000)
