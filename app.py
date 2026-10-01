# ========== app.py：LINE 機器人本體（Colab 跑它、Vercel 也跑它，同一個檔）==========
import os, json, time, math, requests
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)   # 隱藏 line-bot-sdk 舊寫法的「已棄用」警告

from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage, ImageSendMessage, FlexSendMessage
from linebot.models import QuickReply, QuickReplyButton, MessageAction

from weather import earth_quake, weather_data, cctv, CAMERAS
from card import weather_card

access_token = os.environ.get('LINE_TOKEN', '')
channel_secret = os.environ.get('LINE_SECRET', '')
HOME = os.environ.get('HOME_ADDRESS', '雲林縣斗六市')   # 打「天氣」和每天早上推播用的地點

app = Flask(__name__)


def loading(user_id):
    # 讓聊天室出現「…」讀取動畫（免費，不算訊息則數），取代第 3 課的「抓取資料中」推播
    requests.post('https://api.line.me/v2/bot/chat/loading/start',
                  headers={'Authorization': 'Bearer ' + access_token},
                  json={'chatId': user_id, 'loadingSeconds': 10})


def card_message(address, title='現在天氣'):
    d = weather_data(address)
    return FlexSendMessage(alt_text=f"{d['地點']} {d['天氣']} {d['溫度']}°C", contents=weather_card(d, title))


# 打開網址看到這句＝機器人醒著（Vercel 部署完可以用瀏覽器檢查）
@app.route("/", methods=['GET'])
def hello():
    return '機器人醒著 ✅'


# 每當有人傳訊息給機器人，LINE 就會把資料送到這裡
@app.route("/", methods=['POST'])
def linebot():
    body = request.get_data(as_text=True)
    try:
        line_bot_api = LineBotApi(access_token)
        handler = WebhookHandler(channel_secret)
        handler.handle(body, request.headers['X-Line-Signature'])   # 檢查這筆資料真的是 LINE 送來的
        event = json.loads(body)['events'][0]
        reply_token = event['replyToken']
        user_id = event['source']['userId']
        type = event['message']['type']
        print(type, event['message'].get('text', ''))

        # ---- 1. 收到「文字」訊息 ----
        if type == 'text':
            text = event['message']['text']
            if text == '天氣':                               # 新功能：回傳 Flex 天氣卡
                loading(user_id)
                line_bot_api.reply_message(reply_token, card_message(HOME))
            elif text == '雷達回波圖' or text == '雷達回波':
                img_url = f'https://cwaopendata.s3.ap-northeast-1.amazonaws.com/Observation/O-A0058-001.png?{time.time_ns()}'
                line_bot_api.reply_message(reply_token, ImageSendMessage(original_content_url=img_url, preview_image_url=img_url))
            elif text == '監視器':
                buttons = [QuickReplyButton(action=MessageAction(label=name, text=name)) for name in CAMERAS]
                line_bot_api.reply_message(reply_token, TextSendMessage(text='要看哪一個監視器？點下面的按鈕', quick_reply=QuickReply(items=buttons)))
            elif text == '地震' or text == '地震資訊':
                loading(user_id)
                reply = earth_quake()
                messages = [TextSendMessage(text=reply[0])]
                if reply[1] != '':
                    messages.append(ImageSendMessage(original_content_url=reply[1], preview_image_url=reply[1]))
                line_bot_api.reply_message(reply_token, messages)   # 一次回覆最多可以放 5 則訊息
            elif cctv(text) != '':
                url = cctv(text) + f'snapshot?t={math.ceil(time.time())}'   # 監視器的即時截圖網址
                line_bot_api.reply_message(reply_token, [TextSendMessage(text=cctv(text)),
                                                         ImageSendMessage(original_content_url=url, preview_image_url=url)])
            else:
                line_bot_api.reply_message(reply_token, TextSendMessage(text=text))   # 其他文字：學你說話

        # ---- 2. 收到「位置」訊息：回傳那個地方的天氣卡 ----
        elif type == 'location':
            loading(user_id)
            line_bot_api.reply_message(reply_token, card_message(event['message']['address'], '你傳的位置'))
    except Exception as e:
        print(e)
    return 'OK'   # 驗證 Webhook 使用，不能省略


# 每天早上 7 點由 Vercel 自動打開這個網址，把天氣卡推播給所有好友
@app.route("/push", methods=['GET'])
def push():
    secret = os.environ.get('CRON_SECRET', '')
    if secret == '' or request.headers.get('Authorization') != 'Bearer ' + secret:   # 只有 Vercel（或知道密碼的你）能觸發
        return '沒有權限', 401
    LineBotApi(access_token).broadcast(card_message(HOME, '早安！今天的天氣'))
    return '已推播 ✅'
