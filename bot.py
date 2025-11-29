

import os
import re
import random
import time
import aiohttp
from PIL import Image, ImageDraw



from datetime import datetime, timezone, timedelta
from typing import Dict, Tuple, Optional

import nextcord
from nextcord.ext import commands, tasks

from nextcord.ui import View, button
from nextcord import SlashOption

# 訊息檔案路徑
import json
import os


# ---- 近 90 天留言統計（畫圖用） ----
from collections import defaultdict
from datetime import datetime, timedelta

DAILY_MESSAGE_COUNT = defaultdict(int)  # {"2025-01-03": 83, ...}


MESSAGE_FILE = "messages.json"


def load_json(filename):
    if not os.path.exists(filename):
        return {}
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)



def load_messages():
    try:
        print(f"Attempting to load {MESSAGE_FILE}")
        with open(MESSAGE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"Error: The file {MESSAGE_FILE} was not found.")
        return []
    except json.JSONDecodeError:
        print("Error: JSON decode error.")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []


import os
print(f"Current working directory: {os.getcwd()}")
print(f"Checking if messages.json exists: {os.path.exists(MESSAGE_FILE)}")
print(f"Absolute path to messages.json: {os.path.abspath(MESSAGE_FILE)}")
import os
import os
print("Current working directory:", os.getcwd())
print("Checking if messages.json exists:", os.path.exists('./messages.json'))

# Print the current working directory to make sure the path is correct
print(f"Current working directory: {os.getcwd()}")

# Print the content of the current directory to check if messages.json exists
print(f"Listing files in current directory: {os.listdir('.')}")



try:
    with open(MESSAGE_FILE, "r", encoding="utf-8") as f:
        messages = json.load(f)
except json.JSONDecodeError as e:
    print(f"Error decoding JSON: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")




from message_loader import load_messages


# 先載入訊息
messages = load_messages()


# ---- Intents / Bot ----
intents = nextcord.Intents.default()
intents.message_content = True  # 記得在 Developer Portal 開啟 MESSAGE CONTENT INTENT
bot = commands.Bot(command_prefix="!", intents=intents)

# ====== 台北時區（一定要最前面） ======
TAIPEI_TZ = timezone(timedelta(hours=8))

# ====== 當兵專屬設定（你自己的日期） ======
SERVICE_START_DATE = datetime(2025, 12, 1, tzinfo=TAIPEI_TZ)
SERVICE_TOTAL_DAYS = 114
SERVICE_END_DATE = SERVICE_START_DATE + timedelta(days=SERVICE_TOTAL_DAYS - 1)
# =======================================

# ====== 載入 .env（如果有）======
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass



# Discord Token
TOKEN = os.getenv("DISCORD_TOKEN")


# ============================================

from datetime import datetime, timedelta, timezone

TAIWAN_TZ = timezone(timedelta(hours=8))

def is_night_mode():
    now = datetime.now(TAIWAN_TZ)
    return (now.hour >= 23 or now.hour < 3)


# ====== 頻道設定 ======
# 每日固定訊息要發的頻道
DAILY_CHANNEL_ID = 901501574105399396
# 主要聊天頻道
CHAT_CHANNEL_ID = 1387689795148582912
# ======================

NIGHT_MODE_REPLIES = {
    "tired": [
        "…你這語氣，感覺是真的累到心裡去了，你先躺一下，什麼都先別想那麼多( ",
        "深夜的累會比白天放大很多倍，你不用撐著裝沒事，在這邊軟一下也可以( ",
        "嗯…我聽得出來你今天真的過得不太輕鬆，你可以慢慢跟我說到你想停為止就好( "
    ],
    "neutral": [
        "嗯，我在。這個時間如果你還醒著，多少都有一點事放不下對吧( ",
        "這個時間點你還醒著，有點不像平常的你，所以我會多留意你一點( ",
        "深夜的時候講話會不自覺變真，你想講什麼就慢慢丟過來就好( "
    ],
    "comfort": [
        "你先不要急著把情緒整理乾淨，深夜本來就容易把感覺放大，我可以先幫你接著一點( ",
        "我在，你可以邊亂講邊理一下自己的心情，不用一次想清楚，我會跟著你一起聽( ",
        "這種時間點還醒著的人…心裡多少都有東西，我不會逼你講，但你想講的時候我會在( "
    ]
}



# ====== 進階情緒偵測設定（簡易版，不用 GPT） ======
NEGATIVE_KEYWORDS = [
    "好累", "超累", "好煩", "壓力好大", "壓力爆炸",
    "好想哭", "想哭", "心好累", "不想活", "不想面對",
    "好難過", "低落", "好沮喪", "好崩潰",
]

def detect_negative_emotion(text: str) -> bool:
    """簡單檢查句子裡有沒有負面關鍵詞"""
    lower = text.lower()
    return any(kw.lower() in lower for kw in NEGATIVE_KEYWORDS)


# 情緒安慰的隨機句子池（千惠語氣）
EMOTION_RESPONSES = [
    "你這樣講的時候，感覺真的有點撐過頭了…我在，你可以慢慢說，不用一次把所有事講完( ",
    "情緒卡住的時候不要勉強自己，把狀態說出來本身就已經很不容易了，我有認真在聽( ",
    "今天如果過得不太順，也還好吧，你至少願意講出來，代表你還沒放棄自己( ",
    "先讓自己慢下來一點，你不用急著想答案，我先在這裡陪你一下就好( ",
    "你這樣講，感覺你心裡已經累一陣子了…你想從哪個地方開始說？( ",
    "有這種感覺其實不奇怪，反而代表你還在認真面對生活，如果你願意，我可以跟你一起慢慢整理( ",
    "如果今天過得很糟，也沒關係，你能撐到現在就已經很了不起了，接下來可以讓自己鬆一點( ",
    "先深呼吸幾次，讓心跟身體都鬆一點，再決定要不要繼續講，我不會催你( ",
]


# 同一個人情緒回覆的冷卻（秒）避免 bot 太黏人
EMOTION_COOLDOWN_PER_USER = 300  # 5 分鐘
LAST_EMOTION_REPLY_TIME: Dict[int, float] = {}  # {user_id: timestamp}
# ==========================================================
# === 全域情緒關鍵字冷卻 ===
EMOTION_GLOBAL_COOLDOWN = 150  # 秒
emotion_global_cooldown_until = 0  # 時間戳記（冷卻結束時間）

# ---------- 問候詞庫 ----------
GOOD_MORNING_WORDS = ["早安", "早啊", "早上好", "morning"]
GOOD_AFTERNOON_WORDS = ["午安", "午啊", "下午好", "中午好"]
GOOD_NIGHT_WORDS = ["晚安", "晚啊", "good night", "gn"]

# ---------- 問候詞庫 ----------
GOOD_MORNING_WORDS = ["早安", "早啊", "早上好", "morning"]
GOOD_AFTERNOON_WORDS = ["午安", "午啊", "中午好"]
GOOD_NIGHT_WORDS = ["晚安", "晚啊", "good night", "gn"]

# ---------- 冷卻 ----------
GREETING_COOLDOWN = 7200  # 2 小時
greeting_last_trigger = {
    "morning": 0.0,
    "noon": 0.0,
    "night": 0.0,
}

async def handle_greeting_if_any(message):
    if message.author.bot:
        return

    now = time.time()
    content = message.content.lower()

    # 早安
    if any(word in content for word in GOOD_MORNING_WORDS):
        key = "morning"

        if now - greeting_last_trigger[key] >= GREETING_COOLDOWN:
            greeting_last_trigger[key] = now
            await message.reply("早安，你今天還好吧")
        return
    
    # 午安
    if any(word in content for word in GOOD_AFTERNOON_WORDS):
        key = "noon"

        if now - greeting_last_trigger[key] >= GREETING_COOLDOWN:
            greeting_last_trigger[key] = now
            await message.reply("午安，記得喝水")
        return
    
    # 晚安
    if any(word in content for word in GOOD_NIGHT_WORDS):
        key = "night"

        if now - greeting_last_trigger[key] >= GREETING_COOLDOWN:
            greeting_last_trigger[key] = now
            await message.reply("晚安，好好睡")
        return


EMOTION_KEYWORD_REPLIES: Dict[str, str] = {
    "好累": "聽起來是真的有點撐太久了，你要不要先停一下喘口氣，再慢慢跟我講發生什麼事( ",
    "好煩": "那種煩到心裡悶住的感覺，我大概猜得到一點…你想講講看嗎( ",
    "壓力好大": "確實有時候壓力會一下子全部壓上來，你不用馬上把一切處理好，先讓自己穩住比較重要( ",
    "不想動": "還好吧，不想動的時候通常是真的累了，你可以先放著不管一下，等身體比較願意再說也沒關係( ",
    "抱抱": "今天也撐到現在了，你可以不用那麼硬撐，過來這邊一下(抱 ",
    "不想念書": "不想念的時候硬坐在書桌前也進不去，不然你先離開一下，等腦袋沒那麼吵再回來也可以( ",
    "逆天": "逆天",
    "草": "草",
    "開心": "那是肯定的，你開心的話我也會比較放心一點( ",
    "拆家": "能不能別拆了天( ",
    "!西施醬": "嗨，西施醬，你是我們的金主爸爸，我記得你在很早的時候就加入了我們的群組，在群組沉寂了這麼久後，你依舊選擇了加成了這邊，且願意在這邊活躍，感謝你，也希望你在這之後成為我們群組那幾顆最活躍的活躍之星",
    "!炘樘": "炘樘你好，你是我們群偏新的人，但是你很高的活躍讓我馬上就記住你了，我清楚你的魅力所在，也謝謝在剛來的時候看到我狀態不好的時候給了一些情緒支持，也希望你的每天可以像是你最常用的那個貼圖一樣開心",
    "!伊萊": "對伊萊其實有很多想說的，但更多的肯定就是感謝，其實就跟我說的一樣，一開始以為伊萊是個很嚴肅的人，但後來發現伊萊不是嚴肅，一個很可愛很好的女生，伊萊也成為了先鋒隊參與了我的活動，甚至在我當兵的時間段願意接受我「代理群主」的需求，我相信伊萊沒問題的，也希望伊萊天天開心",
    "!夕陽": "嗨我們的群組語音一哥夕陽，你已經在前陣子超越我成為了語音等級最高的人，你高度的人格魅力以及在鬼抓人高度的推理能力都一再讓我的更新了對你的想法，也謝謝你在這群組發生事情的時候，馬上就穩住了我的心態，也期待你可以繼續在未來成為我們的語音跟文字核心",
    "!幻夢": "嗨幻夢，這肯定就是我們的老群員之一了，作為元老級的存在，就算我對幻夢的記憶完全來自於另一個人，但我也清楚幻夢也很熱烈的在默默參與這些活動跟聊天，因此也希望幻夢天天開心",
    "!檸羽": "妳是我們的新晉福利姬，你發的福利只能說非常的有特色，我其實還喜歡那些設定的，你也選擇了這個配色，非常適合你的名字，你成為了我們群組的新核心之一，也期待你可以在這裡有你的一席之地的同時，這裡可以成為你的新出發點",
    "!大熊": "嗨大熊，從慾為到現在，你也伴隨了我們走了很長的路，身為委員會，審核員，我對你的信任近似無限，在發生事情的時候你也是很快就挺身而出為我們說話，你作為少數的四級隊長，你永遠都是群組的核心，希望我能在明年的OOR跟你見面，哈哈哈哈",
    "!眴陽": "嗨眴陽，這是我們的陽哥哥嘛，作為群組金主爸爸的其中之一，超級感謝你給予我們的贊助，也謝謝你一直在語音還有文字聊天的高度活躍，有你在，你就是群組的光亮之一",
    "!辰姐": "你應該我想說的最複雜的其中之一個了，想對你說的話不知道有多少，所以保留到下次現實見面再說吧，感謝你在這群成為了我最好的朋友之一，即使你一直都在開我的玩笑，也願汝桃奔開，別想我哈",
    "!芽": "嗨芽姐姐，第一次與芽見面的時候還是在我們所謂的舊群，當時還不清楚芽是一個多厲害的人，謝謝芽在我機器人遇到一些瓶頸的時候願意幫助我，芽所寫的文章甚至只是負面的歇發，那些文字蘊含的能量並不是三言兩語就能解釋完畢，謝謝芽的照顧捏",
    "!柔柔": "柔柔嗨，可別忘了明年如果有去OOR一定要嘗試約約看，你也是從慾為，到明日，到避難所，這段時間以來一直的見證者，很多話在之前的私訊都說過了，但我對柔柔的謝意可不只是那些，也柔柔也可以繼續當我們避難所「絕對的女王」，能的話，明年見",
    "!柚子": "嗨柚子，你的存在一直讓我都很開心，從你加入之後，群組像是有催化劑一樣，讓我困擾已久的一些問題因為你的到來而解決，我是真的感謝柚子，柚子也是跟我交情多年的朋友，甚至你也曾是看過我和阿城都還是一般群員在別群活躍的那個經歷者，如果有機會的話，下次來台灣，我請柚子吃趟飯（#",
    "!卿卿": "嗨卿卿，在我決定引爆慾為的時候，是你第一個站出來支持我重建慾為，雖然沒有如你所願真的重建了那邊，可我希望避難所不只是慾為的影子，而是能超越那邊的存在，你也不用擔心你脆弱的樣子沒有人願意包容，這裡是你的，我的，我們的，避難所。",
    "!醉艾": "我都不知道你活躍那麼高哈哈哈哈，謝謝醉艾，你是最近期跟我見面的人，還跟我線下喝酒是真的很信任我了，希望醉艾的設計作業可以好好成功，也希望你那個擊敗同宿可以趕緊滾蛋（檢舉你的那個），下次再約妳喝酒，逆天醉艾",
    "!甜了個品": "你很特別，你是在我們前陣子的事件選擇了加入了避難所，且為避難所加入了一些不同以往的味道，不知道你能不能感受到我的用心，但在甜品在這邊待的開心的同時，偶爾也要照顧他人呢，那不是懦弱，而是屬於你的獨一份溫柔",
    "!天奴": "幹我要跟你說什麼，哈哈哈哈，完蛋，你肯定是這個群組裡面跟我相處最久的同位體了，我們都在不同的方位努力，我們都是彼此的投影，也讓彼此都看見了自己有多努力在進步，等我回來，我們一起繼續搞我們的機器人吧，愛你，天奴，謝謝你幫了我很多，也謝謝你帶了我進來這個圈子",
    "!葉卿": "嗨葉卿，感謝你願意跟我分享你的一些私房景點，我找時間一定會去吃吃看，不過那些都要等我退伍之後了，感謝葉卿某一天突然的蹦出來，讓聊天室的一部分染上了屬於葉卿的聲音，我看見你的活躍了，也希望你不要因為課業的迷茫而否定自己",
    "!摸摸": "嗨摸摸，我其實一直很摸不透摸摸是個怎樣的人，但在跟摸摸一起設定摸摸的角色卡的時候，就知道了摸摸是個很可愛且很有個性也很有趣的女孩，即使摸摸說自己是社恐，摸摸也是先鋒隊，也是我的同伴之一，也感謝你願意支持這個避難所，等回來絕對想辦法把刀鋒少女塞進你那邊哈哈哈哈哈",
    "!齊恩": "嗨齊恩，我們私下其實常常也說了很多的，當你發現這個指令的時候，或許你又再次沒有了前進的動力，可是我肯定齊恩所做的一切，我也認為齊恩是很好的朋友，雖然痛苦依舊，雖然依舊不滿現在的生活，我們都努力著讓自己的努力開花，我仍舊相信齊恩終有開花的一天，再怎麼小的理由，那都是我們值得堅持的原因呢",
    "!儒": "對儒哥的感謝太多了，從阿城那時候的慾為四賤客，到現在儒哥都是最支持我的那一份力量，甚至儒哥還願意陪我一起跑場次，那或許對儒哥是一次放鬆（但很累w）的旅程，但對我來講意義重大，謝謝儒哥推薦的板橋拉麵，也期待下次跟儒哥的見面，這次我背負的，就會比以往更多了喔",
    "!穎兒": "嗨穎兒，感謝你在群組一直活躍，也拿了我的活躍之彩，你也成為了避難所的一份子，你的聲音很好聽，聊天的時候給人一種很溫柔的感覺，也感謝你一直高度參與群組的活動，也祝福妳可以繼續在避難所有著自己舒適的溫度",
    "!貓貓": "嗨貓貓，你是我們的福利姬一員的同時，還同時是我們的金主，其實貓貓都隱隱約約的在群組默默活躍，我都有看到喔，想要跟貓貓說，貓貓就是貓貓，你無須被定義，不論別人認為的貓貓是如何的，在避難所的貓貓，就是那個可愛的貓貓，希望這邊也可以讓你待的開心",
    "!蠢蠢": "嗨蠢蠢，雖然你的性癖我有點，沒有涉略w，但我也能感受到蠢蠢用著自己的方法在群組活躍，也謝謝蠢蠢願意當我們的福利姬的同時，還願意加入先鋒隊，你的設定之完整讓我都嘖嘖稱奇，即使我沒有辦法到達蠢蠢的等級，但也希望蠢蠢能在避難所放心的待著",
    "!杏奈": "嗨杏奈，我平常都會跟你私訊聊天，到這種時候反而不知道要跟妳講什麼了，我想說的事情是，杏奈是一個好女孩，不管如何，杏奈很好看，很可愛，也很性感，杏奈在讓自己開心的同時，也讓群組的其他人也開心，不管杏奈遇到了什麼事情，我都希望杏奈能夠開心，而當然，避難所永遠都會有你的一席之地",
    "!Lumi": "嗨Lumi，感謝你在我掉入深淵的時候拉了我一把，即使你不確定我有沒有辦法聽進去，你依舊打了很多話把我從對自己的極度失望硬生生的拉了出來，我想我們早就不是普通的朋友了，不管Lumi對我的想法如何，但我其實很謝謝Lumi願意把我放在心中，我也會盡我的能力，回應你的期待",
    "!阿神": "嗨，你早就不是那三個字了，在這段時間的淬煉下，你早就是那個有極度魅力的人了，阿神總是會給群組帶來歡樂，我知道這裡是阿神第一次踏入這個圈子，但我感覺得到阿神很努力的在融入群組的同時，也認真的把自己當作群組的一部分，這也是我當時選擇了你，而如今，我也相信你可以繼續成長，等我回來時，你或許已經比我耀眼",
    "!九九": "嗨九九，謝謝你在進來沒有多久後就選擇了這個群組加成，我常常看著九九在負面的那些留言，我想說的事情是，迷茫與徬徨都會成為你的一部分，那都是屬於九九的青春，而那些必然難受痛苦的元素，都會使九九的道路更加明確，希望你可要好好加油喔",
    "!炒飯": "嗨炒飯哥，你也是跟著我們的步伐一路來到了避難所，我一直都把炒飯哥視為正能量的來源，雖然不管是城，還是我，可能在炒飯哥的眼裡都是老大，但我知道，炒飯哥永遠都是讓群組開心的那幾個人，也謝謝炒飯選擇了避難所支持",
    "!六本慕": "嗨六哥，從你進入群組以後，我們經歷許多，我想我對六哥的感謝無需多言，此時此刻我只希望六哥所期待的事情如願發生，而我們也可以在避難所內開心的聊天唱歌，做著我們最喜歡的那些事情",
    "!Ansko": "你以為沒有留給你的話嗎，那肯定是有的，你是少數知道我另一個圈子身份的人，也是我極度信任的人，即使我每次都讓你很有距離感，對你來講我可能是重度信用破產用戶，但你的所作所為我都看在眼裡，我知道你有自知，你也認為現在改變太晚，那若改變太晚，我只希望你在規則以內能讓自己在這邊待的開心",
    "!老板": "嗨老板，你以為沒有你嗎，你錯了，感謝老板願意幫我處理那些事情，即使明明就是很簡單的事情，最後卻搞得很複雜呢哈哈哈哈，謝謝老板偶爾會來我的群組聊聊天講講話發發自己的福利，也期待老板下次的再度光臨",
    "!悠悠": "嗨悠悠，謝謝你給我開的那幾堂日文小教室，那對我很有幫助，每次看到悠悠在那邊，開朗（？）爬行的時候我都很想笑，因為我知道你出現了w希望這裡給悠悠也是開心的感覺，也期待我退伍之後，悠悠也可以教會我更多東西",
    "!貓兒": "嗨，貓兒，你應該是名單裡面數一數二很難觸發指令的人了，畢竟你已經消失好長一段時間了，很多話想送給你，你很辛苦了，雖然我在貓兒身上得到了很多既視感，貓兒的重口味福利我也確實迎接不來，但貓兒實在是辛苦了，希望不管彼方，此方即是你的避難所。",
    "!翰": "嗨阿翰，這是我們群內首屈一指的肌肉猛男，只能說男人指數拉爆的你就是其中的佼佼者，不管是福利姬的要求亦又或者語音聊天，從縱慾陪我們走過來的你，也是很誠心的感謝你，也期待你可以繼續在群內為我們的廣大女性送上福利！",
    "!二哈": "嗨二哈，聽說我在準備進去當兵的時候，你剛好可以去你想去的地方實習了，在你去實習的時候也代表你進入了新的一個階段，我知道你在這邊只會找固定的那幾個人聊天，也希望我不在的這段時間，你可以繼續在避難所內找到那幾個與你聊得來的那些人",
    "!語嫣": "嗨可愛的語嫣，當初你進來的時候我認為你可能會是一個極清水及可愛的人，到現在你依舊是這樣的角色，感謝語嫣可以在我們這邊活躍，不管是人設，還是說法的方式，還是你的聊天，都讓我感覺得到你是一位可愛的女孩，這裡也絕對有你的一席之地",
    "!橘子": "嗨橘子，你是這40個人裡面數一數二新的人，雖然妳剛進群的時間不久，但不管是從縱慾那邊的回憶到這邊，我都重視每個群員，也包括了橘子，也希望橘子能在之後開心的在這邊聊天",
    "!玖兒": "呼....嗨，玖兒，如果你有機會觸發這個指令，就代表你可能回來看看了，或許也有可能是想我了w開玩笑的，我對玖兒的印象從你進群的那一刻就有了，到你被某些潛水員私訊騷擾的時候，我也覺得玖兒是個很禮貌很可愛的女孩子，謝謝玖兒常常在我情緒不穩定的時候安慰我，明明相處沒有很久，卻願意把我放在心中，我也把玖兒同樣的放在心底的位子，如果你回來了，那就等我一下吧，我很快就回來了，我還想要，聽關於玖兒更多的事情",
    "!芸樺": "嗨芸樺，不得不說芸樺從個介到說話內容都是一個很有趣的女生，感謝你在有人有需要的時候一起去安撫他的情緒，這群不只有他把你放在他心中重要的位子，你也是我重要的群員其中之一，也希望芸樺可以在避難所開開心心",
    "!西瓜": "嗨西瓜，抱歉一直鴿你玩遊戲的請求，畢竟我大多時候都會有自己想做的事情，西瓜的過去也是都很辛苦，到如今的成果也都是西瓜努力得來的，雖然西瓜會煮飯，會喝酒，打遊戲又很好笑，又很會玩PJSK，但在這些之餘，也要好好照顧自己，雖然退伍後我可能還是會繼續鴿妳，但在這邊，我永遠都保留你的位子",
    "!維藏": "維藏如果好奇為什麼會有自己的話，那是因為維藏畢竟也是這群的元老之一，就算你大多時間在別的群組，我也把你視為這群組的一份子，維藏是個很厲害的人，創建屬於自己的世界，活躍的個性也很可愛，不管如何，避難所的每一位元老，在我心中都有不可替的地位。",
    "!千惠": "那看來各位找尋到真正的彩蛋指令了，當你們觸發到這個指令的時候，我或許正在吃著防彈豬排，正在跑著三千公尺，又或者我已經進入夢鄉，但不管我正在做甚麼，我都很想念你們，想念我可以跟你們一起玩的時光，我不知道觸發指令時會是甚麼時候，但不變的是，我在乎避難所以及所有避難所所有人的心，沒有出現指令的人不代表我不在乎你們，單純只是我時間不足沒辦法做到真的一個一個留言，我知道大家會等待我，那就等我回來，只需耐心等待，我終會走回光裡。",
    "!惠雨": "愛各位，避難所的各位。",



}

GLOBAL_KEYWORD_COOLDOWN = 900  # 全域冷卻秒數
LAST_GLOBAL_TRIGGER = float = 0.0     # 全域上次觸發時間

async def handle_emotion_keywords(message):
    global LAST_GLOBAL_TRIGGER

    content = message.content
    now = time.time()

    # ---------- 0. 檢查全域冷卻 ----------
    if now - LAST_GLOBAL_TRIGGER < GLOBAL_KEYWORD_COOLDOWN:
        return False  # 全域冷卻中 → 不回覆任何敏感詞

    # ---------- 1. 遍歷所有 keyword ----------
    for keyword, reply_text in EMOTION_KEYWORD_REPLIES.items():

        if keyword not in content:
            continue

        # 找到 keyword → 更新全域冷卻
        LAST_GLOBAL_TRIGGER = now

        await message.reply(reply_text)
        return True

    return False



# 冷卻秒數:所有人共用某個關鍵字的冷卻
KEYWORD_COOLDOWN = 150  # 你原本設定的 150 秒

# 每個人收到「冷卻提示」的最小間隔（避免提示也洗版）
HINT_COOLDOWN_PER_USER = 30  # 你原本設定

# 反洗版設定:同一個人同一個關鍵字在冷卻中被提示超過 N 次，就封印一段時間
ABUSE_MAX_HINTS = 1        # 你原本設定
ABUSE_MUTE_SECONDS = 300   # 封印 5 分鐘

# 記錄狀態用的 dict
LAST_REPLY_TIME: Dict[str, float] = {}              # {keyword: timestamp}
LAST_HINT_TIME: Dict[Tuple[str, int], float] = {}   # {(keyword, user_id): timestamp}
MUTE_UNTIL: Dict[Tuple[str, int], float] = {}       # {(keyword, user_id): timestamp}
ABUSE_HINT_COUNT: Dict[Tuple[str, int], int] = {}   # {(keyword, user_id): int}
# ================================

# ====== 每日訊息紀錄（避免重啟後重複發送） ======
LAST_SENT_FILE = "last_sent_date.txt"  # 存在專案資料夾中的小檔案
LAST_SENT_DATE: Optional[str] = None   # 會存 "YYYY-MM-DD"

# ===== 遠征系統設定 =====
BOSS_MAX_HP = 999_999_999_999
boss_current_hp = BOSS_MAX_HP

# 廣域 CD（整個伺服器共用）
EXPEDITION_GLOBAL_COOLDOWN = 180  # 3 分鐘
LAST_EXPEDITION_TIME: float = 0.0  # 上一次任何人使用遠征的時間戳

# 個人 CD（每個人自己的節奏，避免同一個人狂刷）
EXPEDITION_USER_COOLDOWN = 180  # 180 秒，可以自己改
LAST_EXPEDITION_TIME_USER: Dict[int, float] = {}  # {user_id: timestamp}

# 使用者累計傷害統計表 {user_id: total_damage}
USER_DAMAGE_TOTAL: Dict[int, int] = {}

# ====== 真心話大冒險 & 故事接龍 狀態 ======
# 以頻道為單位管理

# 真心話大冒險:{channel_id: set(user_id)}
TOD_PLAYERS: Dict[int, set[int]] = {}

# 故事接龍:
# - STORY_PLAYERS: {channel_id: [user_id1, user_id2, ...]} 固定順序
# - STORY_SENTENCES: {channel_id: {user_id: sentence}}
# - STORY_CURRENT_INDEX: {channel_id: int} 目前輪到第幾個玩家（索引）
STORY_PLAYERS: Dict[int, list[int]] = {}
STORY_SENTENCES: Dict[int, Dict[int, str]] = {}
STORY_CURRENT_INDEX: Dict[int, int] = {}


# ============================================
# 千惠模組包:記憶系統 / 生活化數據 / 反應包 / 早午晚安安靜冷卻 / 每日任務
# ============================================

# ---------- 1. 千惠記憶系統（輕量 JSON） ----------

MEMORY_FILE = "chihye_memory.json"
MEMORY: Dict[str, dict] = {}  # 結構:{"users": {"user_id_str": {"notes": [...], "updated_at": "..."} }}


def load_memory() -> None:
    """啟動時讀取記憶檔，讀不到就用空的。"""
    global MEMORY
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            MEMORY = json.load(f)
            if "users" not in MEMORY:
                MEMORY["users"] = {}
    except (FileNotFoundError, json.JSONDecodeError):
        MEMORY = {"users": {}}


def save_memory() -> None:
    """寫回記憶檔。"""
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(MEMORY, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("save_memory error:", e)


def add_user_note(user_id: int, note: str) -> None:
    """幫某個人多記一則小語錄 / 心情 / 喜歡的東西。"""
    if not note:
        return
    uid = str(user_id)
    users = MEMORY.setdefault("users", {})
    user_mem = users.setdefault(uid, {})
    notes = user_mem.setdefault("notes", [])
    notes.append(note.strip())
    # 最多留 20 則，太久以前的就丟掉
    if len(notes) > 20:
        notes.pop(0)
    user_mem["updated_at"] = datetime.now(TAIPEI_TZ).isoformat(timespec="seconds")
    save_memory()


def get_user_notes(user_id: int):
    uid = str(user_id)
    return MEMORY.get("users", {}).get(uid, {}).get("notes", [])


# ---------- 2. 生活化「伺服器小報告」統計 ----------

USER_MESSAGE_COUNT: Dict[int, int] = {}         # 每個人總訊息數
USER_NIGHT_MESSAGE_COUNT: Dict[int, int] = {}   # 每個人深夜訊息數
CHANNEL_MESSAGE_COUNT: Dict[int, int] = {}      # 每個頻道訊息數


def update_message_stats(message: nextcord.Message) -> None:
    uid = message.author.id
    chid = message.channel.id

    USER_MESSAGE_COUNT[uid] = USER_MESSAGE_COUNT.get(uid, 0) + 1
    CHANNEL_MESSAGE_COUNT[chid] = CHANNEL_MESSAGE_COUNT.get(chid, 0) + 1

    if is_night_mode():
        USER_NIGHT_MESSAGE_COUNT[uid] = USER_NIGHT_MESSAGE_COUNT.get(uid, 0) + 1

    # ★ 記錄每日總量 ★
    day_key = datetime.now(TAIPEI_TZ).strftime("%Y-%m-%d")
    DAILY_MESSAGE_COUNT[day_key] += 1








# ---------- 3. 千惠可愛反應包（輕量版） ----------

REACTION_TRIGGERS = {
    "回來了": [
        "嗯，歡迎回來( ",
        "你回來了喔，那就先在這裡坐一下吧( ",
    ],
    "好無聊": [
        "那要不要玩點什麼？我這邊有一些奇怪的遊戲可以試試看( ",
        "無聊到跑來找我，其實我有一點開心( ",
    ],
    "肚子餓": [
        "那就先去吃東西，聊天可以等，肚子不能等( ",
        "餓著的時候什麼都會變得更煩，先填飽肚子再說( ",
    ],
    "我好冷": [
        "那你多穿一點，或者縮在被子裡，手機可以拿遠一點沒關係( ",
        "冷的時候會特別想有人在旁邊，我暫時先算半個( ",
    ],
}

REACTION_COOLDOWN_PER_USER = 60  # 秒，避免一個人一直觸發
REACTION_LAST_TIME: Dict[int, float] = {}


async def handle_reaction_reply(message: nextcord.Message, now_ts: float) -> bool:
    """可愛反應包:簡單掃關鍵詞，偶爾回一句。回傳是否有回覆。"""
    # 只在主要聊天頻道開啟
    if message.channel.id not in (CHAT_CHANNEL_ID, DAILY_CHANNEL_ID):
        return False

    uid = message.author.id
    text = message.content

    # 簡單防洗:每人 60 秒一次
    last = REACTION_LAST_TIME.get(uid, 0.0)
    if now_ts - last < REACTION_COOLDOWN_PER_USER:
        return False

    for kw, replies in REACTION_TRIGGERS.items():
        if kw in text:
            reply = random.choice(replies)
            # 深夜稍微柔一點
            if is_night_mode():
                reply = reply.replace("？", "…？")
            await message.channel.send(f"{message.author.mention} {reply}")
            REACTION_LAST_TIME[uid] = now_ts
            return True

    return False


# ---------- 4. 早安 / 午安 / 晚安:2 小時安靜冷卻 ----------

GREETING_COOLDOWN = 7200  # 2 小時
GREETING_LAST_TIME: Dict[str, float] = {
    "早安": 0.0,
    "午安": 0.0,
    "晚安": 0.0,
}

# ---------- 問候詞庫 ----------
GOOD_MORNING_WORDS = ["早安", "早啊", "早上好", "morning"]
GOOD_AFTERNOON_WORDS = ["午安", "午啊", "中午好"]
GOOD_NIGHT_WORDS = ["晚安", "晚啊", "good night", "gn"]

# ============================================
# ❤️ 情緒模組 v3（全域 CD + 個人 CD + 封印 + 深夜模式）
# ============================================

# 🔥 全域冷卻（所有關鍵字共用）
EMOTION_GLOBAL_COOLDOWN = 150  # 秒
emotion_global_cooldown_until = 0.0

async def handle_emotion_keywords(message, now_ts):
    """
    處理:
    - 敏感字關鍵字回覆
    - 封印（反濫用）
    - 個人提示冷卻
    - 全域冷卻
    - 深夜模式
    """

    global emotion_global_cooldown_until

    content = message.content
    user_id = message.author.id

    # 🌍 0) 全域冷卻
    if now_ts < emotion_global_cooldown_until:
        return False

    # 🔍 1) 搜尋所有關鍵字
    for keyword, reply_text in EMOTION_KEYWORD_REPLIES.items():

        if not is_keyword_triggered(keyword, content):
            continue

        user_key = (keyword, user_id)

        # 🌙 2) 深夜模式切換內容
        if is_night_mode() and keyword in ["好累", "好煩", "壓力好大", "不想動", "不想念書"]:
            reply_text = random.choice(NIGHT_MODE_REPLIES["tired"])

        # 🚫 3) 檢查是否被封印
        mute_until = MUTE_UNTIL.get(user_key, 0)
        if now_ts < mute_until:
            return True  # 已經封印，不回覆

        # 🧊 4) 單字冷卻（個別 keyword 冷卻）
        last_time = LAST_REPLY_TIME.get(keyword, 0)
        elapsed = now_ts - last_time

        if elapsed < KEYWORD_COOLDOWN:
            # 單字冷卻 → 檢查提示冷卻
            last_hint = LAST_HINT_TIME.get(user_key, 0)

            if now_ts - last_hint >= HINT_COOLDOWN_PER_USER:
                LAST_HINT_TIME[user_key] = now_ts

                # 計算濫用次數
                count = ABUSE_HINT_COUNT.get(user_key, 0) + 1
                ABUSE_HINT_COUNT[user_key] = count

                # 尚未到封印門檻 → 顯示剩餘冷卻
                if count < ABUSE_MAX_HINTS:
                    remain = int(KEYWORD_COOLDOWN - elapsed)
                    await message.channel.send(
                        f"{message.author.mention} 這個關鍵字還在冷卻中，大概 {remain} 秒後再試比較好( "
                    )
                else:
                    # 超過次數 → 直接封印
                    MUTE_UNTIL[user_key] = now_ts + ABUSE_MUTE_SECONDS
                    await message.channel.send(
                        f"{message.author.mention} 你這樣有點太頻繁了，不然先停一下吧( "
                    )
            return True

        # 🎉 5) 正常回覆
        await message.channel.send(f"{message.author.mention} {reply_text}")

        # 更新個別冷卻
        LAST_REPLY_TIME[keyword] = now_ts
        ABUSE_HINT_COUNT[user_key] = 0

        # 🔥 6) 設定全域冷卻！（重點）
        emotion_global_cooldown_until = now_ts + EMOTION_GLOBAL_COOLDOWN

        return True

    return False


AVATAR_SIZE = 64
AVATAR_PADDING = 16   # 頭貼之間的間距
COLUMNS = 5           # 一排 5 個頭貼
ROWS = 2              # 共兩排，最多 10 人


async def fetch_image_bytes(url: str) -> bytes:
    """下載圖片成 bytes（用來抓頭貼）"""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.read()


def circle_crop(image: Image.Image, size: int) -> Image.Image:
    """把頭貼裁成圓形並調整大小"""
    image = image.resize((size, size), Image.LANCZOS).convert("RGBA")
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)
    image.putalpha(mask)
    return image


async def build_top10_image(bot, guild, top10):
    """
    建立 Top10 合照圖。
    top10: list[(user_id, count)]
    回傳 PIL Image 物件
    """
    width = COLUMNS * AVATAR_SIZE + (COLUMNS + 1) * AVATAR_PADDING
    height = ROWS * AVATAR_SIZE + (ROWS + 1) * AVATAR_PADDING
    bg_color = (20, 20, 24)  # 深色背景

    canvas = Image.new("RGBA", (width, height), bg_color)

    for idx, (user_id, _count) in enumerate(top10):
        row = idx // COLUMNS
        col = idx % COLUMNS

        x = AVATAR_PADDING + col * (AVATAR_SIZE + AVATAR_PADDING)
        y = AVATAR_PADDING + row * (AVATAR_SIZE + AVATAR_PADDING)

        # 優先從 guild 找成員
        member = guild.get_member(int(user_id))
        avatar_url = None
        if member:
            avatar_url = member.display_avatar.url
        else:
            try:
                user = await bot.fetch_user(int(user_id))
                avatar_url = user.display_avatar.url
            except Exception:
                avatar_url = None

        if not avatar_url:
            # 沒有頭貼就跳過（或放一個預設圖也可以）
            continue

        try:
            data = await fetch_image_bytes(avatar_url)
            avatar_img = Image.open(io.BytesIO(data))
            avatar_img = circle_crop(avatar_img, AVATAR_SIZE)
            canvas.paste(avatar_img, (x, y), avatar_img)
        except Exception:
            # 單一失敗不影響整張圖
            continue

    return canvas


# ---------- 5. 每日任務（今日小任務） ----------

DAILY_MISSIONS = [
    "今天找一個時間，認真喝完一整杯水。",
    "刻意對某個人說一句『謝謝』，哪怕只是很小的事。",
    "允許自己發呆三分鐘，什麼都不做也可以。",
    "把手機放下五分鐘，只聽一下周圍的聲音。",
    "跟一個人說『辛苦了』，不一定要解釋原因。",
    "睡前對自己說一句『今天這樣就夠了』。",
]


def get_mission_for_today() -> str:
    today_str = datetime.now(TAIPEI_TZ).strftime("%Y-%m-%d")
    # 用日期字串做一個穩定的 index，避免每天重啟任務亂跳
    idx = sum(ord(c) for c in today_str) % len(DAILY_MISSIONS)
    return DAILY_MISSIONS[idx]


@bot.command(name="mission", aliases=["今日任務", "任務"])
async def mission_cmd(ctx: commands.Context):
    m = get_mission_for_today()
    await ctx.send(f"{ctx.author.mention} 今天的任務是:{m}")





def get_expedition_comment(damage: int) -> str:
    """
    根據這次的傷害，給一句千惠式旁白。
    混合版:
    - 很低傷害:特別嘴一點
    - 中間區間:微壞、偏溫和
    - 接近爆擊:有點像在檢查你最近是不是壓力太大
    """

    # 超級低傷害:0～10，特別嘴
    if damage <= 10:
        pool = [
            "這一下…老實說可能我真的沒感覺，你是來暖場的嗎( ",
            "我開始懷疑你是不是忘了拔安全鎖，這數字有點太溫柔了( ",
            "如果只看這傷害，我會以為你只是在做瑜珈輕拍按摩( ",
            "如果不看戰鬥紀錄，我會以為你只是揮到自己影子而已( ",
        ]

    # 非常低但至少看得懂是攻擊:11～49
    elif damage < 50:
        pool = [
            "這一下大概是提醒我世界上還有人存在的程度而已( ",
            "蚊子如果認真一點，可能還會比這更痛一點( ",
            "勉強可以算是有在揮，但戰鬥紀錄看起來滿像意外按到的( ",
        ]

    # 小力區:50～199
    elif damage < 200:
        pool = [
            "有打到，不過比較像在幫我把灰塵拍掉，還沒進入戰鬥狀態( ",
            "這數字…好啦，至少證明你真的有在線，而不是純聊天( ",
            "算是輕輕敲牆壁示意『我在這裡』的那種力度( ",
            "算是輕輕敲了一下桌面，吵不到我睡覺那種級別( ",
        ]

    # 微妙區:200～499
    elif damage < 500:
        pool = [
            "這力度勉強可以叫一刀，我可能只會覺得哪裡有點癢( ",
            "這傷害或許還可以，不過應該還不足以讓我記住你是誰( ",
            "有認真揮了，只是目前還在暖身環節，正式開打應該不只這樣吧( ",
            "這種傷害…如果當作熱身，其實還算合理( ",
        ]

    # 還行區:500～999
    elif damage < 1000:
        pool = [
            "這傷害還行，至少不會被誤會成是系統判定誤差( ",
            "我看到這個數字，大概會抬頭看你一眼，然後繼續做原本的事( ",
            "好歹可以稱作一個完整的攻擊了，再上去一點就有存在感了( ",
        ]

    # 中等輸出:1000～2999
    elif damage < 3000:
        pool = [
            "這一下總算有點認真了，我應該會開始記得你是有在打的那種人( ",
            "以這個數字來說，再穩定幾次，我可能會開始後悔沒早點處理你( ",
            "這種傷害如果持續輸出，久了真的會讓我覺得人生有點累，雖然我本來就很累了( ",
        ]

    # 中高輸出:3000～5999
    elif damage < 6000:
        pool = [
            "這傷害有點兇，我之後回想今天大概會想到你這一刀( ",
            "這一發已經完全脫離娛樂區了，正式進入『會痛』的範圍( ",
            "以這個程度來說，你再多揮幾次我大概會開始本能往後退( ",
        ]

    # 高輸出:6000～8999
    elif damage < 9000:
        pool = [
            "這一刀很實在，我現在應該會把你列進優先處理名單裡( ",
            "這數字看起來就不像在玩，我認真記一下你的 ID( ",
            "這樣打幾次，我可能會開始懷疑是不是哪裡設定錯誤才讓你長這樣( ",
            "這數字根本就不是辦家家酒呢，我應該會認真開始考慮防守你這方向( ",
        ]

  

    # 接近滿傷害:9000～10000，精神狀況關心版
    else:
        pool = [
            "這數字看起來像是在拿 Boss 出氣，你最近是不是壓力有點大( ",
            "這一發有點像是把好幾天的情緒一起丟進去，你要不要順便講講最近怎樣( ",
            "這傷害很漂亮沒錯，只是…你這樣揮，我會稍微擔心你是不是需要休息一下( ",
        ]

    return random.choice(pool)
# =======================


def load_last_sent_date() -> None:
    """啟動時從檔案讀取上次已發訊息的日期（如果有）"""
    global LAST_SENT_DATE
    try:
        with open(LAST_SENT_FILE, "r", encoding="utf-8") as f:
            date_str = f.read().strip()
            if date_str:
                LAST_SENT_DATE = date_str
    except FileNotFoundError:
        LAST_SENT_DATE = None


def save_last_sent_date(date_str: str) -> None:
    """送出當日訊息後，寫入檔案，避免之後重啟重複發"""
    with open(LAST_SENT_FILE, "w", encoding="utf-8") as f:
        f.write(date_str)
# ==================================================


def get_today_message() -> Optional[str]:
    """
    從 messages.json 讀取今天要發的長文日記
    依照 date 欄位比對 YYYY-MM-DD，若有 title 就一起顯示
    """
    today_str = datetime.now(TAIPEI_TZ).strftime("%Y-%m-%d")
    try:
        with open("messages.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        for entry in data:
            if entry.get("date") == today_str:
                title = entry.get("title", "")
                content = entry.get("content", "")
                if title and content:
                    return f"{title}\n\n{content}"
                elif content:
                    return content
                elif title:
                    return title
                else:
                    return None

        # 找不到對應日期
        return None
    except FileNotFoundError:
        print("⚠️ 找不到 messages.json，將改用預設訊息")
        return None
    except Exception as e:
        print("讀取 messages.json 發生錯誤:", e)
        return None



def is_keyword_triggered(keyword: str, text: str) -> bool:
    """
    只在「訊息開頭」是關鍵字時觸發，例如:
    早安
    早安～
    早安 大家
    不會對「大家早安」「昨天忘了說早安」觸發
    """
    text = text.strip().lower()
    kw = keyword.lower()
    pattern = rf"^{re.escape(kw)}($|\s|[!！?.。～,，…]+)"
    return re.match(pattern, text) is not None


@bot.event
async def on_ready():
    print(f"✅ 已登入:{bot.user} (ID: {bot.user.id})")
    if not send_daily_message.is_running():
        send_daily_message.start()
        daily_reset_task.start()
        weekly_report_task.start()
        monthly_report_task.start()
        print("統計系統已啟動。")



@bot.event
async def on_message(message):

    # ==================================================
    # 0) 忽略機器人自己
    # ==================================================
    if message.author.bot:
        return

    now_ts = int(time.time())
    content = message.content
    channel_id = message.channel.id
    responded = False

    # ==================================================
    # 1) 侷限互動功能只在聊天頻道 & 每日頻道（你原本的設定）
    # ==================================================
    if channel_id in (CHAT_CHANNEL_ID, DAILY_CHANNEL_ID):

        # ----------------------------------------------
        # (1) 深夜模式檢查（你原本的結構）
        # ----------------------------------------------
        if is_night_mode():
            if detect_negative_emotion(content):
                await message.channel.send(
                    random.choice(NIGHT_MODE_REPLIES["tired"])
                )
                return

        # ----------------------------------------------
        # (2) 情緒關鍵字系統（🔥 全域 CD + 個人 CD + 封印）
        # ----------------------------------------------
        if not responded:
            if await handle_emotion_keywords(message, now_ts):
                responded = True

        # ----------------------------------------------
        # (3) 問候系統（早安 / 午安 / 晚安）
        # ----------------------------------------------
        if not responded:
            if await handle_greeting_if_any(message):
                responded = True

    # ==================================================
    # 2) 讓 bot 的指令正常運作
    # ==================================================
    await bot.process_commands(message)



async def resolve_user_info(bot, guild, user_id: int):
    # 1. 先找伺服器成員
    member = guild.get_member(user_id)
    if member:
        return {
            "name": member.display_name,
            "mention": member.mention,
            "avatar": member.display_avatar.url
        }

    # 2. 伺服器找不到 → 向 Discord API 查詢
    try:
        user = await bot.fetch_user(user_id)
        return {
            "name": user.global_name or user.name,
            "mention": user.mention,  # 不在伺服器，用名字即可
            "avatar": user.display_avatar.url
        }
    except Exception:
        return {
            "name": "未知使用者",
            "mention": "未知使用者",
            "avatar": None
        }



@bot.command()
async def top(ctx: commands.Context):

    if not os.path.exists("user_message_counts.json"):
        await ctx.send("紀錄檔案不存在… 我沒法算排行榜( ")
        return

    with open("user_message_counts.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    if not data:
        await ctx.send("目前還沒有任何留言紀錄( ")
        return

    ranking = sorted(data.items(), key=lambda x: x[1], reverse=True)

    
    user_ids_ordered = [int(uid) for uid, _ in ranking]


    # Top 10 & Top 25
    top10 = ranking[:10]
    top25 = ranking[:25]

    user_idsordered = [int(uid) for uid, _ in ranking]
    author_id = ctx.author.id

    if author_id in user_ids_ordered:
        self_rank = user_ids_ordered.index(author_id) + 1
        self_count = data.get(str(author_id), 0)
        self_text = f"你目前是第 {self_rank} 名，累積 {self_count} 則留言。"
    else:
        self_rank = None
        self_text = "你目前還沒上榜，不然多跟大家聊聊天看看( "

    if self_rank == 1:
        color = 0xFFD700  # 金
    elif self_rank == 2:
        color = 0xC0C0C0  # 銀
    elif self_rank == 3:
        color = 0xCD7F32  # 銅
    else:
        color = 0xFFCC66  # 普通暖色

    embed = nextcord.Embed(title="按一下以了解更多 〈伺服器留言排行榜 Top 25〉",
        description=(
            "「我每天都在看著你們講話啦……所以我做了這個。欸… "
            "我偷偷整理的啦，你們不要笑我。」\n\n"
            + self_text
        ),
        color=color,
    )


    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    lines = []

    for idx, (user_id, count) in enumerate(top10, start=1):
        member = ctx.guild.get_member(int(user_id))

        if member:
            name_display = member.display_name
        else:
            try:
                user = await bot.fetch_user(int(user_id))
                name_display = user.global_name or user.name
            except Exception:
                name_display = "未知使用者"

        medal = medals.get(idx, f"#{idx}")
        lines.append(f"{medal} {name_display} — {count} 則")

    embed.add_field(name="Top 10", value="\n".join(lines), inline=False)


    if self_rank and self_rank > 10 and self_rank <= 25:
        embed.add_field(
            name="你的位置",
            value=f"你在前 25 名裡，目前是第 {self_rank} 名。",
            inline=False,
        )

    embed.set_footer(text="「你們每天講話的樣子… 我都在旁邊看著。真的。謝謝你們一直讓伺服器這麼熱鬧。」")

    img = await build_top10_image(bot, ctx.guild, top10)


    with io.BytesIO() as image_binary:
        img.save(image_binary, format="PNG")
        image_binary.seek(0)
        file = nextcord.File(fp=image_binary, filename="top10.png")
        embed.set_image(url="attachment://top10.png")

        await ctx.send(file=file, embed=embed)
    


@tasks.loop(minutes=1)
async def daily_reset_task():
    now = datetime.now()
    if now.hour == 0 and now.minute == 0:
        save_json("user_message_today.json", {})
        print("每日統計已重置。")



@tasks.loop(minutes=1)
async def weekly_report_task():
    now = datetime.now()

    # 週日 23:59 發佈排行
    if now.weekday() == 6 and now.hour == 23 and now.minute == 59:
        data = load_json("user_message_week.json")
        if not data:
            return

        # 排名
        ranking = sorted(data.items(), key=lambda x: x[1], reverse=True)[:10]

        # 公告頻道
        channel = bot.get_channel(YOUR_CHANNEL_ID)

        msg = "📘 **本週千惠觀察日誌（Top 10）**\n\n"
        for i, (uid, count) in enumerate(ranking, start=1):
            msg += f"**{i}.** <@{uid}> — **{count} 則**\n"

        msg += "\n（我都看在眼裡啦，大家記得喝水。）"

        await channel.send(msg)

        # 重置
        save_json("user_message_week.json", {})
        print("每週統計已重置。")


@tasks.loop(minutes=1)
async def monthly_report_task():
    now = datetime.now()
    tomorrow = now + timedelta(days=1)

    # 判斷是否月末（23:59）
    if tomorrow.month != now.month and now.hour == 23 and now.minute == 59:
        data = load_json("user_message_month.json")
        if not data:
            return

        # 排名前15
        ranking = sorted(data.items(), key=lambda x: x[1], reverse=True)[:15]

        # 公告頻道
        channel = bot.get_channel(YOUR_CHANNEL_ID)

        msg = "📙 **本月千惠觀察報告（Top 15）**\n\n"
        for i, (uid, count) in enumerate(ranking, start=1):
            msg += f"**{i}.** <@{uid}> — **{count} 則**\n"

        msg += "\n（下個月也…一起加油吧。）"

        await channel.send(msg)

        # 重置
        save_json("user_message_month.json", {})
        print("每月統計已重置。")




# 啟動時就先把記憶載進來
load_memory()

@bot.command(name="我的留言", aliases=["我講了多少", "個人統計", "留言數"])
async def personal_stats(ctx: commands.Context):
    """顯示個人的留言統計。"""

    uid = ctx.author.id

    total = USER_MESSAGE_COUNT.get(uid, 0)
    night = USER_NIGHT_MESSAGE_COUNT.get(uid, 0)

    # 如果完全沒有紀錄
    if total == 0:
        await ctx.send(f"{ctx.author.mention} 你在這裡講話還太少，我根本抽不出你的樣子啦( ")
        return

    # ------ 計算排名 ------
    sorted_users = sorted(
        USER_MESSAGE_COUNT.items(), key=lambda x: x[1], reverse=True
    )
    rank = next((i for i, (u, _) in enumerate(sorted_users, start=1) if u == uid), None)

    # ------ 千惠式分析 ------
    rank_comment = ""
    if rank == 1:
        rank_comment = "…你是這裡最吵的那個，我每天都看得到你，但謝了w( "
    elif rank <= 5:
        rank_comment = "你一直都是活躍的那幾個呢…我其實一直知道你很常來找大家講話呢( "
    elif rank <= 15:
        rank_comment = "還可以吧，但沒事啦，我看得出你偶爾會忙啦，有空再來就好( "
    else:
        rank_comment = "中後段，會讓我覺得你是不是太累了，還好你偶爾會來找我一下( "

    night_comment = ""
    if night > 30:
        night_comment = "還有…你深夜講話真的很多，你是不是都不睡覺？記得要多睡覺捏( "
    elif night > 10:
        night_comment = "深夜訊息有一點，但還不算太誇張…不可以太晚睡啦，我會生氣喔( "
    else:
        night_comment = "深夜很少看到你，這樣比較好，至少你睡得比我放心( "

    embed = nextcord.Embed(
        title=f"📘 你的個人留言統計",
        color=0xFFB7C5
    )

    embed.add_field(name="你的總留言數", value=f"{total} 則", inline=False)
    embed.add_field(name="你的排名", value=f"第 **{rank} 名**", inline=False)
    embed.add_field(name="深夜留言", value=f"{night} 則", inline=False)

    embed.add_field(
        name="千惠偷偷補一句:",
        value=f"{rank_comment}\n{night_comment}",
        inline=False
    )

    await ctx.send(embed=embed)




@bot.command(name="dailytest")
async def dailytest(ctx):
    """
    測試今天的每日訊息內容（不受排程影響，只是預覽）
    """
    msg = get_today_message()
    if msg is None:
        await ctx.send("今天在 messages.json 裡沒有找到對應的內容 QQ")
    else:
        await ctx.send(f"【今日預覽】\n{msg}")




@bot.command(name="遠征")
async def expedition(ctx: commands.Context, *, skill: str = None):
    """
    遠征指令:!遠征 / !遠征 技能名字
    - 廣域 CD:全伺服器共用
    - 個人 CD:每個人自己的冷卻
    - 傷害隨機 1～10000，並記錄累計傷害
    - 在冷卻中使用會:刪掉訊息 + 私訊剩餘秒數
    """
    global boss_current_hp, LAST_EXPEDITION_TIME, LAST_EXPEDITION_TIME_USER, USER_DAMAGE_TOTAL

    now = datetime.now().timestamp()
    user_id = ctx.author.id

    # ---- 冷卻檢查:廣域 + 個人 ----
    global_elapsed = now - LAST_EXPEDITION_TIME
    user_last = LAST_EXPEDITION_TIME_USER.get(user_id, 0.0)
    user_elapsed = now - user_last

    global_remain = EXPEDITION_GLOBAL_COOLDOWN - global_elapsed
    user_remain = EXPEDITION_USER_COOLDOWN - user_elapsed

    # 只要有一個還在冷卻，就算無效攻擊
    if global_remain > 0 or user_remain > 0:
        # 要提醒的秒數取「兩者裡剩比較久的那一個」
        remain = int(max(global_remain, user_remain, 0))

        # 1) 刪掉頻道裡的那則指令訊息（避免洗版）
        try:
            await ctx.message.delete()
        except nextcord.Forbidden:
            pass
        except nextcord.HTTPException:
            pass

        # 2) 私訊告訴他還要等多久
        try:
            if remain < 1:
                remain = 1
            await ctx.author.send(f"遠征還在冷卻中，大概 **{remain}** 秒之後才能再攻擊( ")
        except nextcord.Forbidden:
            # 對方關閉私訊就算了，不額外處理
            pass

        return  # 冷卻中就不繼續往下執行

    # ---- 通過冷卻檢查，正式攻擊 ----
    LAST_EXPEDITION_TIME = now
    LAST_EXPEDITION_TIME_USER[user_id] = now

    damage = random.randint(1, 10000)
    boss_current_hp = max(0, boss_current_hp - damage)

    # 累計傷害記錄
    USER_DAMAGE_TOTAL[user_id] = USER_DAMAGE_TOTAL.get(user_id, 0) + damage

    # 技能文字
    if skill:
        skill_text = f"「{skill}」"
    else:
        skill_text = "隨手揮了一下"

    # 千惠式旁白（只看傷害）
    comment = get_expedition_comment(damage)

    # 組合訊息:
    msg = (
        f"{ctx.author.mention} {skill_text}，"
        f"對 Boss 造成了 **{damage}** 點傷害，"
        f"Boss 剩餘 **{boss_current_hp} / {BOSS_MAX_HP}** HP，"
        f"{comment}"
    )

    await ctx.send(msg)

@bot.command(name="遠征排行")
async def expedition_rank(ctx: commands.Context):
    """
    查看遠征傷害排行（Top 10，如果自己不在 Top 10，會另外顯示自己的名次）
    """
    if not USER_DAMAGE_TOTAL:
        await ctx.send("目前還沒有任何人造成傷害( ")
        return

    # 排行:照傷害高到低
    ranking = sorted(USER_DAMAGE_TOTAL.items(), key=lambda x: x[1], reverse=True)

    embed = nextcord.Embed(
        title="《遠征傷害排行》",
        description="前 10 名的累積輸出狀況",
        color=0xF5B642,
    )

    lines = []
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}

    for i, (user_id, dmg) in enumerate(ranking[:10], start=1):
        medal = medals.get(i, f"{i}.")
        mention = f"<@{user_id}>"
        lines.append(f"{medal} {mention}:**{dmg}** 點")

    embed.add_field(
        name="Top 10",
        value="\n".join(lines),
        inline=False,
    )

    # 如果自己不在 Top 10，額外顯示自己的名次
    user_ids_ordered = [uid for uid, _ in ranking]
    if ctx.author.id in user_ids_ordered:
        self_rank = user_ids_ordered.index(ctx.author.id) + 1
        self_total = USER_DAMAGE_TOTAL.get(ctx.author.id, 0)

        if self_rank > 10:
            embed.add_field(
                name="你的位置",
                value=f"你目前是第 **{self_rank}** 名，累積 **{self_total}** 點傷害( ",
                inline=False,
            )
        else:
            # 在 Top 10 裡就用 footer 提醒一下
            embed.set_footer(
                text=f"你目前在前 10 名裡，第 {self_rank} 名，累積 {self_total} 點傷害( "
            )

    await ctx.send(embed=embed)


class TodView(View):
    """真心話大冒險控制台用的按鈕 View"""

    def __init__(self, channel_id: int):
        super().__init__(timeout=None)
        self.channel_id = channel_id

    @button(label="加入遊戲", style=nextcord.ButtonStyle.blurple)
    async def join_button(self, _: nextcord.ui.Button, interaction: nextcord.Interaction):
        channel_id = self.channel_id
        players = TOD_PLAYERS.setdefault(channel_id, set())

        if interaction.user.id in players:
            await interaction.response.send_message("你已經在這輪名單裡了( ", ephemeral=True)
        else:
            players.add(interaction.user.id)
            await interaction.response.send_message("我幫你加進真心話大冒險了( ", ephemeral=True)

    @button(label="退出遊戲", style=nextcord.ButtonStyle.gray)
    async def leave_button(self, _: nextcord.ui.Button, interaction: nextcord.Interaction):
        channel_id = self.channel_id
        players = TOD_PLAYERS.setdefault(channel_id, set())

        if interaction.user.id in players:
            players.remove(interaction.user.id)
            await interaction.response.send_message("好，我先把你從這輪名單裡拿掉( ", ephemeral=True)
        else:
            await interaction.response.send_message("你本來就不在這輪名單裡( ", ephemeral=True)

    @button(label="查看玩家", style=nextcord.ButtonStyle.gray)
    async def list_button(self, _: nextcord.ui.Button, interaction: nextcord.Interaction):
        channel_id = self.channel_id
        players = TOD_PLAYERS.get(channel_id, set())

        if not players:
            await interaction.response.send_message("目前還沒有人加入這輪真心話大冒險( ", ephemeral=True)
            return

        mentions = [f"<@{uid}>" for uid in players]
        text = "這一輪的玩家:\n" + "\n".join(mentions)
        await interaction.response.send_message(text, ephemeral=True)

    @button(label="下一回合", style=nextcord.ButtonStyle.green)
    async def next_round_button(self, _: nextcord.ui.Button, interaction: nextcord.Interaction):
        channel_id = self.channel_id
        players = TOD_PLAYERS.get(channel_id, set())

        # 只有「有加入的玩家」可以按
        if interaction.user.id not in players:
            await interaction.response.send_message("你目前沒有加入這輪，不能幫大家抽下一回合( ", ephemeral=True)
            return

        if len(players) < 2:
            await interaction.response.send_message("至少要兩個人加入才有辦法抽出題者跟被懲罰者( ", ephemeral=True)
            return

        player_list = list(players)
        questioner = random.choice(player_list)

        # 被懲罰者不能跟出題者同一個人
        possible_targets = [uid for uid in player_list if uid != questioner]
        target = random.choice(possible_targets)

        embed = nextcord.Embed(
            title="🎲 真心話大冒險 - 本回合結果",
            color=0x57F287,  # 綠色系
        )
        embed.add_field(name="出題者", value=f"<@{questioner}>", inline=True)
        embed.add_field(name="被懲罰者", value=f"<@{target}>", inline=True)
        embed.set_footer(text="出題者可以決定是真心話還是大冒險( ")

        # 公開公告在頻道裡
        await interaction.response.send_message(embed=embed)


@bot.command(name="tod", aliases=["真心話大冒險"])
async def truth_or_dare(ctx: commands.Context):
    """
    真心話大冒險控制台:
    - 按鈕加入/退出
    - 查看目前玩家
    - 下一回合:隨機抽出題者與被懲罰者
    """
    channel_id = ctx.channel.id
    # 每次開一個新的控制台時，不會清掉舊玩家，方便連續玩
    TOD_PLAYERS.setdefault(channel_id, set())

    embed = nextcord.Embed(
        title="🎲 真心話大冒險 控制台",
        description=(
            "・按「加入遊戲」就會被加進這一輪名單\n"
            "・按「退出遊戲」可以先離開\n"
            "・按「查看玩家」可以看到目前名單\n"
            "・只有有加入的人可以按「下一回合」\n\n"
            "按下「下一回合」後，會從名單裡抽一個出題者，"
            "再抽一個被懲罰者，並在頻道公告結果( "
        ),
        color=0xF5B642,
    )

    view = TodView(channel_id=channel_id)
    await ctx.send(embed=embed, view=view)


class StoryView(View):
    """故事接龍控制台用的按鈕 View"""

    def __init__(self, channel_id: int):
        super().__init__(timeout=None)
        self.channel_id = channel_id

    @button(label="加入故事", style=nextcord.ButtonStyle.blurple)
    async def join_button(self, _: nextcord.ui.Button, interaction: nextcord.Interaction):
        channel_id = self.channel_id
        players = STORY_PLAYERS.setdefault(channel_id, [])

        if interaction.user.id in players:
            await interaction.response.send_message("你已經在這輪故事接龍名單裡了( ", ephemeral=True)
            return

        players.append(interaction.user.id)
        await interaction.response.send_message("好，我把你加進故事接龍這一輪了( ", ephemeral=True)

    @button(label="退出故事", style=nextcord.ButtonStyle.gray)
    async def leave_button(self, _: nextcord.ui.Button, interaction: nextcord.Interaction):
        channel_id = self.channel_id
        players = STORY_PLAYERS.setdefault(channel_id, [])

        if interaction.user.id in players:
            players.remove(interaction.user.id)
            # 如果退出的人剛好是之後索引的人，就讓 index 自動調整一下
            idx = STORY_CURRENT_INDEX.get(channel_id, 0)
            if idx >= len(players):
                STORY_CURRENT_INDEX[channel_id] = max(0, len(players) - 1)
            await interaction.response.send_message("好，我先把你從這輪裡拿掉( ", ephemeral=True)
        else:
            await interaction.response.send_message("你本來就不在這輪故事裡( ", ephemeral=True)

    @button(label="查看玩家", style=nextcord.ButtonStyle.gray)
    async def list_button(self, _: nextcord.ui.Button, interaction: nextcord.Interaction):
        channel_id = self.channel_id
        players = STORY_PLAYERS.get(channel_id, [])

        if not players:
            await interaction.response.send_message("目前還沒有人加入故事接龍( ", ephemeral=True)
            return

        mentions = [f"<@{uid}>" for uid in players]
        text = "這一輪的順序是:\n" + "\n".join(
            f"{i+1}. {m}" for i, m in enumerate(mentions)
        )
        await interaction.response.send_message(text, ephemeral=True)

    @button(label="下一位", style=nextcord.ButtonStyle.green)
    async def next_turn_button(self, _: nextcord.ui.Button, interaction: nextcord.Interaction):
        channel_id = self.channel_id
        players = STORY_PLAYERS.get(channel_id, [])

        # 只有有加入的玩家可以按
        if interaction.user.id not in players:
            await interaction.response.send_message("你沒有加入這輪故事接龍，不能幫大家推進( ", ephemeral=True)
            return

        if not players:
            await interaction.response.send_message("這裡目前還沒有任何玩家，沒辦法進行( ", ephemeral=True)
            return

        # 目前輪到第幾個
        idx = STORY_CURRENT_INDEX.get(channel_id, 0)

        # 如果 index 等於玩家數量代表已經跑完一輪，可以結算
        if idx >= len(players):
            sentences_map = STORY_SENTENCES.get(channel_id, {})
            if not sentences_map or len(sentences_map) < len(players):
                await interaction.response.send_message(
                    "看起來還有人沒造句完，先等全部人都用 /story_write 之後再按結算比較好( ",
                    ephemeral=True,
                )
                return

            # 結算:依照玩家順序列出句子
            lines = []
            story_parts = []
            for i, uid in enumerate(players, start=1):
                sentence = sentences_map.get(uid, "（這個人沒有寫東西）")
                lines.append(f"{i}. <@{uid}>:{sentence}")
                story_parts.append(sentence)

            full_story = " ".join(story_parts) if story_parts else "（沒內容）"

            embed = nextcord.Embed(
                title="📖 故事接龍 - 本輪故事結算",
                color=0x5865F2,
            )
            embed.add_field(
                name="每個人的句子",
                value="\n".join(lines),
                inline=False,
            )
            embed.add_field(
                name="組合起來的完整故事",
                value=full_story,
                inline=False,
            )
            embed.set_footer(text="故事接龍結束，如果要再玩一輪可以繼續用這個控制台( ")

            # 公開結算
            await interaction.response.send_message(embed=embed)

            # 重置這一輪的進度 & 內容，但保留玩家順序方便再玩一輪
            STORY_SENTENCES[channel_id] = {}
            STORY_CURRENT_INDEX[channel_id] = 0
            return

        # 還在一輪中，宣布現在輪到誰
        current_user_id = players[idx]
        mention = f"<@{current_user_id}>"

        msg = (
            f"現在輪到 {mention} 造句了。\n\n"
            "・你可以先使用 `/story_prev` 來查看「上一位玩家」的內容\n"
            "・再使用 `/story_write 句子: ...` 來寫下你要接的那一句\n\n"
            "其他人看不到內容，只有當這一輪全部跑完後才會結算出完整故事( "
        )

        await interaction.response.send_message(msg)





@bot.command(name="story", aliases=["故事接龍"])
async def story_game(ctx: commands.Context):
    """
    故事接龍控制台:
    - 按鈕加入/退出/查看玩家/下一位
    - 造句用 /story_prev + /story_write
    """
    channel_id = ctx.channel.id

    # 如果首次建立此頻道的故事資料，就初始化
    STORY_PLAYERS.setdefault(channel_id, [])
    STORY_SENTENCES.setdefault(channel_id, {})
    STORY_CURRENT_INDEX.setdefault(channel_id, 0)

    embed = nextcord.Embed(
        title="📖 故事接龍 控制台",
        description=(
            "・按「加入故事」來加入這一輪故事接龍\n"
            "・按「退出故事」可以先離開\n"
            "・按「查看玩家」可以看目前輪到順序\n"
            "・按「下一位」會宣布目前輪到誰造句\n\n"
            "輪到你的時候:\n"
            "1. 用 `/story_prev` 看上一位玩家的句子\n"
            "2. 再用 `/story_write 句子: ...` 來寫下你的句子\n\n"
            "只有輪到的那個人看得到上一句，大家的內容會在整輪結束後一次公布( "
        ),
        color=0x5865F2,
    )

    view = StoryView(channel_id=channel_id)
    await ctx.send(embed=embed, view=view)


@bot.slash_command(
    name="story_prev",
    description="查看上一位玩家的句子（只有輪到你時才能看）",
)
async def story_prev(interaction: nextcord.Interaction):
    channel = interaction.channel
    if channel is None:
        await interaction.response.send_message("這個指令只能在文字頻道裡用( ", ephemeral=True)
        return

    channel_id = channel.id
    players = STORY_PLAYERS.get(channel_id, [])
    idx = STORY_CURRENT_INDEX.get(channel_id, 0)

    if not players:
        await interaction.response.send_message("這個頻道目前沒有進行中的故事接龍( ", ephemeral=True)
        return

    # 只有目前輪到的那個人可以看上一句
    if idx >= len(players):
        await interaction.response.send_message("這一輪已經跑完了，如果要看內容請等結算( ", ephemeral=True)
        return

    current_user_id = players[idx]
    if interaction.user.id != current_user_id:
        await interaction.response.send_message("現在還不是輪到你，所以你看不到上一句( ", ephemeral=True)
        return

    # 第一位沒有上一句
    if idx == 0:
        await interaction.response.send_message("你是開頭，沒有上一句，可以自由開頭( ", ephemeral=True)
        return

    prev_user_id = players[idx - 1]
    sentences_map = STORY_SENTENCES.get(channel_id, {})
    prev_sentence = sentences_map.get(prev_user_id)

    if not prev_sentence:
        await interaction.response.send_message("上一位還沒寫完，所以目前沒有內容可以給你看( ", ephemeral=True)
        return

    await interaction.response.send_message(
        f"上一位玩家 <@{prev_user_id}> 的句子是:\n{prev_sentence}",
        ephemeral=True,
    )


@bot.slash_command(
    name="story_write",
    description="為這一輪的故事接龍寫下你的句子",
)
async def story_write(
    interaction: nextcord.Interaction,
    sentence: str = SlashOption(
        name="句子",
        description="你要接上的那一句話",
        required=True,
    ),
):
    channel = interaction.channel
    if channel is None:
        await interaction.response.send_message("這個指令只能在文字頻道裡用( ", ephemeral=True)
        return

    channel_id = channel.id
    players = STORY_PLAYERS.get(channel_id, [])
    idx = STORY_CURRENT_INDEX.get(channel_id, 0)

    if not players:
        await interaction.response.send_message("這個頻道目前沒有進行中的故事接龍( ", ephemeral=True)
        return

    if interaction.user.id not in players:
        await interaction.response.send_message("你沒有加入這一輪故事接龍，沒辦法在這邊造句( ", ephemeral=True)
        return

    if idx >= len(players):
        await interaction.response.send_message("這一輪已經跑完了，可以請人按「下一位」做結算( ", ephemeral=True)
        return

    current_user_id = players[idx]
    if interaction.user.id != current_user_id:
        await interaction.response.send_message("現在還不是輪到你，等等再來寫會比較好( ", ephemeral=True)
        return

    sentences_map = STORY_SENTENCES.setdefault(channel_id, {})

    # 避免同一輪重複覆蓋，同一個人只能寫一次
    if interaction.user.id in sentences_map:
        await interaction.response.send_message("你這一輪已經寫過了，如果真的想改，只能請管理員重開一輪( ", ephemeral=True)
        return

    # 記錄句子
    sentences_map[interaction.user.id] = sentence.strip()
    STORY_SENTENCES[channel_id] = sentences_map

    # 前進到下一位
    STORY_CURRENT_INDEX[channel_id] = idx + 1

    await interaction.response.send_message("我先幫你把這一句記起來了( ", ephemeral=True)



@bot.command()
async def ping(ctx: commands.Context):
    """測試用指令:!ping"""
    await ctx.send(f"{ctx.author.mention} 在，在的，別懷疑( ")

@bot.command(name="今日小報告", aliases=["今日報告", "伺服器小報告"])
async def today_report(ctx: commands.Context):
    """千惠的當日伺服器小報告。"""

    # 如果沒有任何紀錄
    if not USER_MESSAGE_COUNT:
        await ctx.send("欸…我今天好像還沒看到什麼東西，再陪我說說話啦( ")
        return

    # 今日總訊息量
    total_messages = sum(USER_MESSAGE_COUNT.values())

    # Top talkers（前 10 名）
    top_talkers = sorted(USER_MESSAGE_COUNT.items(), key=lambda x: x[1], reverse=True)[:10]

    # Top 深夜講話（前 5 名）
    top_night = sorted(USER_NIGHT_MESSAGE_COUNT.items(), key=lambda x: x[1], reverse=True)[:5]

    # 最吵的頻道（前 5 名）
    top_channels = sorted(CHANNEL_MESSAGE_COUNT.items(), key=lambda x: x[1], reverse=True)[:5]

    # 今天最常 tag 別人的人
    tag_count: Dict[int, int] = {}
    for uid, data in MEMORY.get("today_tags", {}).items():
        tag_count[int(uid)] = data

    top_taggers = sorted(tag_count.items(), key=lambda x: x[1], reverse=True)[:5]

    # 今天最常找千惠的人
    today_chihui_calls = MEMORY.get("today_chihui", {})  # {uid: 次數}
    top_chihui_callers = sorted(today_chihui_calls.items(), key=lambda x: x[1], reverse=True)[:3]

    # 千惠式旁白（隨機）
    comments = [
        "我都在旁邊偷偷看著啦，你們真的很吵，但…有點可愛( ",
        "今天伺服器的氣氛還不錯，我喜歡這樣的感覺( ",
        "你們今天是不是又偷熬夜，去睡覺啦笨蛋( ",
        "我覺得你們講話講的比我在軍中跑步還累欸( ",
    ]

    import random
    comment = random.choice(comments)

    embed = nextcord.Embed(
        title="📊 《千惠的當日伺服器小報告》",
        description=comment,
        color=0xFFC03A,
    )

    # 總量
    embed.add_field(
        name="📝 今日總訊息量",
        value=f"{total_messages} 則",
        inline=False,
    )

    # Top talkers
    talker_lines = []
    for uid, count in top_talkers:
        talker_lines.append(f"<@{uid}>:{count} 則")
    embed.add_field(
        name="💬 今天講最多話的人（前十名）",
        value="\n".join(talker_lines) if talker_lines else "無資料",
        inline=False,
    )

    # 深夜不睡覺
    night_lines = []
    for uid, count in top_night:
        night_lines.append(f"<@{uid}>:{count} 則")
    embed.add_field(
        name="🌙 深夜不睡覺榜（前 5 名）",
        value="\n".join(night_lines) if night_lines else "大家都有乖乖睡( ",
        inline=False,
    )

    # 頻道
    channel_lines = []
    for chid, count in top_channels:
        channel_lines.append(f"<#{chid}>:{count} 則")
    embed.add_field(
        name="📢 今天最吵的頻道（前 5 名）",
        value="\n".join(channel_lines) if channel_lines else "今天伺服器特別安靜欸( ",
        inline=False,
    )

    # 最常 tag 人
    tag_lines = []
    for uid, count in top_taggers:
        tag_lines.append(f"<@{uid}>:{count} 次")
    embed.add_field(
        name="📎 今天最常 tag 別人的人",
        value="\n".join(tag_lines) if tag_lines else "今天大家好像都很低調欸( ",
        inline=False,
    )

    # 最常找千惠
    chihui_lines = []
    for uid, count in top_chihui_callers:
        chihui_lines.append(f"<@{uid}>:{count} 次")
    embed.add_field(
        name="💗 今天最常找千惠的人",
        value="\n".join(chihui_lines) if chihui_lines else "沒人找我…好孤單||個毛||( ",
        inline=False,
    )

    await ctx.send(embed=embed)




import matplotlib.pyplot as plt
import io

@bot.command(name="留言走勢", aliases=["訊息走勢", "伺服器走勢"])
async def message_trend(ctx: commands.Context):

    # 若統計量太少
    if len(DAILY_MESSAGE_COUNT) < 3:
        await ctx.send("欸……目前資料還有點少，我再觀察一陣子再給你看好不好( ")
        return

    # 取近 90 天
    today = datetime.now(TAIPEI_TZ).date()
    days_ago_90 = today - timedelta(days=90)

    # 過濾區間
    filtered = {
        day: count
        for day, count in DAILY_MESSAGE_COUNT.items()
        if datetime.strptime(day, "%Y-%m-%d").date() >= days_ago_90
    }

    # 排序
    sorted_days = sorted(filtered.keys())
    x = sorted_days
    y = [filtered[day] for day in sorted_days]

    # 畫圖
    plt.figure(figsize=(10, 4))
    plt.plot(x, y, linewidth=2)
    plt.xticks(rotation=45, fontsize=8)
    plt.title("近 90 天留言走勢圖", fontsize=14)
    plt.tight_layout()

    # 存到 BytesIO
    img_bytes = io.BytesIO()
    plt.savefig(img_bytes, format="png")
    img_bytes.seek(0)
    plt.close()

    file = nextcord.File(img_bytes, filename="msg_trend.png")

    # 千惠語氣
    await ctx.send(
        "欸我這段時間在旁邊看你們鬧得蠻開心的，給你看一下最近 90 天的留言走勢( ",
        file=file
    )

@bot.command()
async def draw(ctx: commands.Context):
    """簡單小占卜:!draw（包含 1% 彩蛋籤）"""

    fortunes = [

    # 1–10:大吉・溫柔哲學版
    "大吉:今天的你像是突然對世界解鎖了什麼隱藏 buff，一切都會順得不太真實。",
    "大吉:連風吹到你都很溫柔的一天，真的不太常見…你就先收下吧。",
    "大吉:你今天會莫名被善待，那不是偶然，是世界終於良心發現。",
    "大吉:你大概會連走路都踩在舒服的地方上，有點好笑但又確實挺好的。",
    "大吉:你今天的存在感比平常柔軟很多，身邊的人可能會突然注意到你。",
    "大吉:你今天的運勢跟你睡醒的髮型一樣，不知道為什麼但就是很順。",
    "大吉:你今天適合把事情做完、把喜歡說出口…反正世界會偏向你。",
    "大吉:這是會讓你覺得『欸？好像不錯？』的一天。",
    "大吉:你看看，偶爾被幸運摸一下頭也是挺好的。",
    "大吉:你今天像是小說裡那種突然變得很能幹的角色，不過放心，不會超出常理。",
    
    # 11–20:中吉・溫柔安靜系
    "中吉:你會遇到一點好事，像放在口袋裡的小糖果那種，不張揚但甜。",
    "中吉:今天的你比較像是會讓人安心的存在，可是你大概不知道。",
    "中吉:你可能會被輕輕治癒一下，理由不明，但你值得。",
    "中吉:雖然不會大爆炸，但會有幾件事比平常順很多。",
    "中吉:你今天比較像月光那種，好看但不刺眼。",
    "中吉:會有人無意間對你很好，你會裝沒事但心裡偷偷收著。",
    "中吉:某些小困擾會自己散掉，你不用出力。",
    "中吉:你今天也許會被誰肯定一下，你大概會逃走，但我知道你會開心。",
    "中吉:你今天會突然覺得世界沒有那麼壞，算是進步。",
    "中吉:你今天有點像慢慢融化的奶油，可愛但你不知道。",
    
    # 21–35:吉・日常無奈 + 千惠風格
    "吉:你今天像被太陽曬過的床單，乾淨舒服，但看起來普通。",
    "吉:你的情緒會維持在『還好吧』的狀態，這比想像中珍貴。",
    "吉:你今天會覺得某些事很煩，但還在你能忍耐的範圍裡。",
    "吉:你可能會小小被誇，但你會假裝沒聽到。",
    "吉:今天是普通的一天，但普通也算一種幸福…雖然你應該不會承認。",
    "吉:你今天的運勢像未攪拌均勻的奶茶，有一點甜有一點怪，但能喝。",
    "吉:你今天的思緒會比平常清楚…一點點啦。",
    "吉:你適合安靜處理事情，反正喧鬧也不會變更好。",
    "吉:你今天會覺得某些人很可愛，雖然你不會說。",
    "吉:你可能會突然想做點什麼，去做吧，別猶豫。",
    "吉:你今天比較像『差一步會更好』的那種…但差一步也沒關係啦。",
    "吉:你可能會突然有靈感，但只有三秒。",
    "吉:今天適合溫柔，也適合被溫柔一下。",
    "吉:如果有人問你在想什麼，你大概會說沒有，但其實一堆。",
    "吉:你今天是那種會被小小事情治癒的體質。",
    
    # 36–50:小吉・自嘲可愛系
    "小吉:你的運勢像是忘記密碼卻突然想起來那種水準，微妙但不錯。",
    "小吉:你今天會突然意識到自己其實挺堅強的…雖然你還是不信。",
    "小吉:你可能會突然想把房間整理一下，但只會整理五分鐘。",
    "小吉:你今天的幸運是那種會讓你『嗯…好像還行？』的等級。",
    "小吉:會有人對你稍微好一點，你會裝冷靜。",
    "小吉:今天適合喝點甜的，像是在安慰你一樣。",
    "小吉:你可能會突然覺得自己有點可愛…放心，沒人會發現。",
    "小吉:你今天會比平常有點勇敢，但只是一點點。",
    "小吉:你今天比較像漫畫裡背景卻突然變重要的角色。",
    "小吉:你今天會想逃避某些事，但其實沒那麼可怕。",
    "小吉:會有人突然找你，但不是壞事。可能只是想跟你講廢話。",
    "小吉:你會突然想得太多，但還在可控範圍。",
    "小吉:你今天適合溫柔待自己一次，不然我會念你。",
    "小吉:你的努力會被看到，只是你大概會假裝不在意。",
    "小吉:你今天有點像輕飄飄的棉花糖，沒特別好，但很軟。",
    
    # 51–65:小凶・無奈系
    "小凶:今天會有點煩，不到崩潰，就是那種『唉』的程度。",
    "小凶:你會覺得很多事情都卡卡的，但勉強能動。",
    "小凶:有人可能會誤會你，但你應該懶得解釋。",
    "小凶:你會被小事絆一下腳，不會痛，但會皺眉。",
    "小凶:今天適合不要跟傻子理論，你會輸得很難看。",
    "小凶:你會突然覺得一切都沒必要，其實你只是累。",
    "小凶:你會覺得別人講話聽起來很吵，但你還是會回。",
    "小凶:你今天的狀態像網速慢半秒，有夠煩。",
    "小凶:你可能會莫名覺得孤單，但那只是腦袋在耍廢。",
    "小凶:今天不適合大動作，會出事。",
    "小凶:你沒做錯什麼，但還是會被誰念一下。",
    "小凶:你今天適合保持安靜，會比較平安。",
    "小凶:你今天可能會心累，但你還是會把事情做完。",
    "小凶:你會想逃避一切，但你還活著，這已經很厲害了。",
    "小凶:你今天適合深呼吸三次，不要跟世界吵架。",
    
    # 66–75:凶前段・千惠嘴硬溫柔版
    "凶:你今天可能會被誰氣到，但你還是會笑笑地忍過去…我知道。",
    "凶:有些事會讓你想說『不太對吧？』但你會吞下來。",
    "凶:你今天比較像一台快沒電的手機，想做事但跑不動。",
    "凶:你會突然覺得世界在針對你，但那只是巧合…大概啦。",
    "凶:你今天會想把所有訊息都關靜音，我懂。",
    "凶:今天不是很友善，但至少不會毀滅級。",
    "凶:你可能會講出一句讓自己後悔的話，但沒人會在意。",
    "凶:你今天適合躲起來一會兒，不然會更煩。",
    "凶:你會覺得很累，但你還是會把責任扛完…像往常一樣。",
    "凶:你今天的心比較脆，但表面看不出來。"  

        # 76–85:吉系食物梗（可愛惡搞）
    "吉:你今天的運勢像吉野家牛丼，普通但暖心，只是沒有加蛋有點可惜。",
    "吉:你今天的能量像剛炸好的吉拿棒，脆脆甜甜的，但咬下去會掉一地糖粉那種。",
    "吉:你的心情像吉娃娃，莫名有點敏感，但看起來又很想被抱一下。",
    "吉:你今天的運勢像便利商店的吉利丁，看起來沒用，但料理裡少了它就怪。",
    "吉:你今天像吉祥物，站在那裡什麼也不做，也會讓人覺得安心。",
    "吉:你今天的魅力像日式吉列豬排，厚實、安靜、被咬到會幸福那種。",
    "吉:你今天像吉他社，會突然想彈一下什麼情緒，但三秒後又放下。",
    "吉:你的日常像吉備團子，有點黏、有點甜、不驚艷但讓人喜歡。",
    "吉:你今天像吉野家加大碗，但店員忘記加蔥…有好也有遺憾。",
    "吉:你今天像吉祥天女，沒做什麼卻會被誇一句好看。",

    # 86–95:凶系食物梗（但不傷人）
    "凶:你今天的運勢像吃到沒有沾醬的臭豆腐，微妙又難形容。",
    "凶:你今天像泡麵忘記放調味粉，整體直接往下掉兩級。",
    "凶:你今天像不小心買錯地雷口味的御飯糰，吃了會反省人生。",
    "凶:你今天像放到隔天的薯條，軟軟爛爛但還是吃得下。",
    "凶:你今天像加太多芥末的壽司，醒腦但會讓你後悔。",
    "凶:你的情緒像買到冷掉的雞塊，知道該吃但提不起勁。",
    "凶:你今天像撞到桌角，不至於痛到哭，但會罵一句靠。",
    "凶:你今天像忘記搖的珍奶，甜味全沉底，不均衡得很惱人。",
    "凶:你的狀態像焦掉一點點的鬆餅，看起來正常但吃起來怪。",
    "凶:你今天很像三倍辣泡麵，整個人都在燒，連我看了都痛。",

    # 96–110:千惠壞壞罵人籤（壞但不傷人）
    "凶:你今天講話的邏輯有點像睡三小時的人…我建議你先喝水。",
    "凶:你今天看起來很像在放空，但我知道你只是懶得動。",
    "凶:你今天的反應比我還慢，這不太對吧？",
    "凶:你今天可能會講一句你自己都聽不懂的話，然後假裝沒事。",
    "凶:你今天的運氣爛到我都想幫你按 reset。",
    "凶:你今天的情緒像沒更新的系統，卡得很固執。",
    "凶:我覺得你今天很像要跟世界吵架，但拜託冷靜一點。",
    "凶:你今天的靈魂有點離線，能不能快點回來？",
    "凶:你今天可能會把怪罪給天氣…我懂啦。",
    "凶:你今天很像在跟氧氣吵架，深呼吸一下啦。",

    # 111–125:千惠反常（但可愛）
    "凶:你今天的氣質跟平常不太一樣…該不會是睡壞了？",
    "凶:你今天特別像吉娃娃那種，想凶又凶不起來。",
    "凶:你今天會突然有小暴脾氣，但只維持五秒。",
    "凶:你今天聽起來比平常更無奈…有點好笑。",
    "凶:你今天跟人講話的語氣奇妙地像長輩，稍微收斂一下。",
    "凶:你今天的沉默比平常吵…發生什麼事了？",
    "凶:你今天某個瞬間會像 NPC 卡牆，完全動不了。",
    "凶:你今天會突然想變厲害，但三分鐘後就忘記。",
    "凶:你今天會想把手機摔掉，但你不會捨得。",
    "凶:你今天會想講狠話，但你講不出口。",

    # 126–140:輕哲學系（淡淡無奈）
    "平:你今天會突然懷疑自己是不是把什麼情緒弄丟了。",
    "平:今天適合慢慢講、慢慢聽，快的話你會迷路。",
    "平:你今天會突然覺得某些事不值得生氣，算是醒悟。",
    "平:你今天的心很軟，但那不是壞事。",
    "平:你今天適合跟自己和解一點點。",
    "平:有些事你今天沒想通，但明天會突然懂。",
    "平:你今天的靈魂比較安靜，但沒有悲傷。",
    "平:今天會有人理解你，但你可能不會察覺。",
    "平:你今天適合做些不重要的小事，反而會心安。",
    "平:你今天的世界會慢一拍，但不會讓你受傷。",
    "平:你今天會突然覺得『這樣也可以』，這蠻好的。",
    "平:你今天的存在有種慢慢亮起來的感覺。",
    "平:你今天適合把事情分兩次做，不急。",
    "平:你今天的思緒像漏水的水龍頭，一滴一滴但不停。",
    "平:今天適合跟自己相處，你會發現自己沒想像中糟。",

    # 141–150:千惠特色梗（你原本味道 + 升級）
    "吉:千惠的手晃了一下，覺得你今天勉強算是不錯的。",
    "吉:你今天像在跟命運玩抽卡，但你只抽到 R 卡…不過可愛。",
    "吉:你今天有點像想睡但睡不著的貓咪，無奈的可愛。",
    "吉:你今天會被誰影響心情，但你會假裝沒有。",
    "吉:你今天像被人不小心摸頭，但你會假裝沒感覺。",
    "吉:你今天的存在像 Wi-Fi 三格，還能用但不太穩。",
    "吉:你今天會讓誰在心裡偷偷重播你一句話。",
    "吉:你今天會讓人覺得你安靜得像在藏什麼，但你沒有。",
    "吉:你今天的沉默比平常有意思，我不確定為什麼。",
    "吉:你今天的狀態是千惠判定:嗯…還好吧。",
]

        


      

    # ★ 1% 彩蛋籤（獨立出來）
    secrets = [
        # --- 1〜4:哲學爆擊（深得不像占卜）
        "今天不是世界在對你溫柔，是你終於願意承認自己值得了。",
        "你一直在找答案，但很多事情只是需要被放過…包括你自己。",
        "有些痛苦不是來傷你的，是來提醒你『你還活著』。",
        "你今天可能會突然懂得一件很難的事，但代價是你會更沉默一點。",

        # --- 5〜7:反常千惠（怪到靠北）
        "我剛剛算了一下，你今天的運勢跟外太空訊號同頻……你小心點。",
        "你等一下不要回頭，有點不對勁…啊沒事，是我搞錯了。",
        "今天的一切都會變得很奇怪，但你會假裝正常，這點我最欣賞。",

        # --- 8〜10:搞笑千惠（突然變弱智）
        "你今天的運勢像我凌晨打字時的手——完全不受控，也不知道在幹嘛。",
        "你今天可能會被自己的影子嚇到，我不會笑…真的不會（噗）。",
        "你今天的腦袋會突然當機，但重開之後會更笨一點，抱歉我只能說實話。",

        # --- 11〜15:壞壞千惠（壞但不傷人）
        "你今天要是再懶一點，可能連呼吸都想委外代工。",
        "你的思緒今天會亂到讓我懷疑你昨天到底做了什麼。",
        "你今天如果講幹話，我會比平常更快看穿…只是懶得拆穿你。",
        "你今天的情緒會黏著你不放，就像你黏著那些不值得的人。",
        "如果今天有人惹你生氣，你先冷靜…因為你真的會把對方嗆死。",

    ]

# ★ 1% 機率抽彩蛋簽
    if random.random() < 0.01:
        choice = random.choice(secrets)
    else:
        choice = random.choice(fortunes)

    await ctx.send(f"{ctx.author.mention} 抽到的是:{choice}")


async def send_message_for_today(channel: nextcord.TextChannel) -> bool:
    """
    在指定頻道發送今天的訊息。
    回傳 True 表示有成功發文。
    """
    global LAST_SENT_DATE
    now = datetime.now(TAIPEI_TZ)
    today_str = now.strftime("%Y-%m-%d")
    today_date = now.date()

    msg = get_today_message()
    if msg is None:
        msg = "今天沒有預設訊息，但還是祝你有美好的一天！🌞"

    # 加上當兵專屬資訊（只有在服役期間內才顯示）
    if SERVICE_START_DATE.date() <= today_date <= SERVICE_END_DATE.date():
        day_index = (today_date - SERVICE_START_DATE.date()).days + 1  # 第幾天
        days_left = (SERVICE_END_DATE.date() - today_date).days
        msg += f"\n\n今天是當兵的第 {day_index} 天，距離結束還有 {days_left} 天，加油 💪"

    await channel.send(msg)

    LAST_SENT_DATE = today_str
    save_last_sent_date(today_str)
    return True


@tasks.loop(minutes=1)
async def send_daily_message():
    """
    每分鐘檢查一次，到了 08:00 就在 DAILY_CHANNEL_ID 發文。
    如果當天已經發過（包含補發），就不會重複發。
    """
    global LAST_SENT_DATE

    now = datetime.now(TAIPEI_TZ)
    today_str = now.strftime("%Y-%m-%d")

    # 已經發過就不再處理
    if LAST_SENT_DATE == today_str:
        return

    if now.hour == 8 and now.minute == 0:
        channel = bot.get_channel(DAILY_CHANNEL_ID)
        if channel is None:
            print("❌ 找不到每日訊息頻道 DAILY_CHANNEL_ID，請確認 ID 是否正確")
            return

        await send_message_for_today(channel)


@send_daily_message.before_loop
async def before_send_daily_message():
    """
    排程開始前:
    1. 等待 bot 準備完成
    2. 嘗試從檔案載入上次已發日期
    3. 如果「現在已經超過 8:00，且今天還沒發過」，就自動補發一次
    """
    print("⏳ 等待 Bot 準備完成後啟動排程…")
    await bot.wait_until_ready()
    load_last_sent_date()

    now = datetime.now(TAIPEI_TZ)
    today_str = now.strftime("%Y-%m-%d")

    # 如果已經過了今天 8:00，而且 LAST_SENT_DATE 不是今天 → 補發一次
    if LAST_SENT_DATE != today_str and (now.hour > 8 or (now.hour == 8 and now.minute > 0)):
        channel = bot.get_channel(DAILY_CHANNEL_ID)
        if channel is not None:
            print("⚠️ 檢測到啟動時間已晚於 8:00，準備補發今日訊息一次。")
            await send_message_for_today(channel)
        else:
            print("❌ 找不到每日訊息頻道 DAILY_CHANNEL_ID（補發階段），請確認 ID 是否正確。")

    print("🕒 排程已啟動。")


if __name__ == "__main__":
    if not TOKEN:
        raise RuntimeError("找不到 DISCORD_TOKEN 環境變數，請在 Railway / 本機環境設定它。")
    bot.run(TOKEN)

# ============================================================
# 真心話大冒險 TOD 系統
# ============================================================

import random
import nextcord
from nextcord.ext import commands
from nextcord import Interaction, SlashOption, ui

class TODView(ui.View):
    def __init__(self, players):
        super().__init__(timeout=None)
        self.players = players

    @ui.button(label="加入", style=nextcord.ButtonStyle.blurple)
    async def join(self, button: ui.Button, interaction: Interaction):
        if interaction.user.id not in self.players:
            self.players.append(interaction.user.id)
            await interaction.response.send_message(f"{interaction.user.mention} 已加入遊戲！", ephemeral=True)
        else:
            await interaction.response.send_message("你已經在遊戲裡了！", ephemeral=True)

    @ui.button(label="退出", style=nextcord.ButtonStyle.grey)
    async def leave(self, button: ui.Button, interaction: Interaction):
        if interaction.user.id in self.players:
            self.players.remove(interaction.user.id)
            await interaction.response.send_message(f"{interaction.user.mention} 已退出遊戲！", ephemeral=True)
        else:
            await interaction.response.send_message("你不在玩家名單中。", ephemeral=True)

    @ui.button(label="下一回合", style=nextcord.ButtonStyle.green)
    async def next_round(self, button: ui.Button, interaction: Interaction):
        if len(self.players) < 2:
            await interaction.response.send_message("需要至少兩位玩家才能開始（出題者與被懲罰者）！", ephemeral=True)
            return

        asker = random.choice(self.players)
        target = random.choice(self.players)
        while target == asker:
            target = random.choice(self.players)

        asker_mention = f"<@{asker}>"
        target_mention = f"<@{target}>"

        


        embed = nextcord.Embed(
    title="🎲 真心話大冒險 下一回合！",
    description=(
        f"🧩 **出題者**:{asker_mention}\n"
        f"🎯 **被懲罰者**:{target_mention}"
    ),
    color=0x00ff88,
)

        await interaction.response.send_message(embed=embed)


class TOD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.players = []  # TOD 玩家列表

    @nextcord.slash_command(name="tod", description="開始真心話大冒險遊戲")
    async def tod(self, interaction: Interaction):
        view = TODView(self.players)
        embed = nextcord.Embed(
            title="🎉 真心話大冒險",
            description="按下按鈕加入遊戲吧！",
            color=0xff66cc
        )
        await interaction.response.send_message(embed=embed, view=view)


# ============================================================
# 故事接龍 Story 系統（整理修復後完整版）
# ============================================================

class StoryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.players = []
        self.sentences = {}
        self.turn = 0
        self.started = False

    @nextcord.slash_command(name="story", description="故事接龍主介面")
    async def story(self, interaction: Interaction):
        embed = nextcord.Embed(
    title="📖 故事接龍",
    description=(
        "使用 /story_add_player 加入遊戲\n"
        "使用 /story_start 開始接龍"
    ),
    color=0x88ccee
)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @nextcord.slash_command(name="story_add_player", description="加入故事接龍")
    async def story_add(self, interaction: Interaction):
        if interaction.user.id not in self.players:
            self.players.append(interaction.user.id)
            await interaction.response.send_message("你已加入故事接龍！", ephemeral=True)
        else:
            await interaction.response.send_message("你已在名單中。", ephemeral=True)

    @nextcord.slash_command(name="story_remove_player", description="退出故事接龍")
    async def story_remove(self, interaction: Interaction):
        if interaction.user.id in self.players:
            self.players.remove(interaction.user.id)
            await interaction.response.send_message("你已退出故事接龍。", ephemeral=True)
        else:
            await interaction.response.send_message("你不在名單中。", ephemeral=True)

    @nextcord.slash_command(name="story_start", description="開始故事接龍")
    async def story_start(self, interaction: Interaction):
        if len(self.players) < 2:
            await interaction.response.send_message("至少需要兩位玩家才能開始！", ephemeral=True)
            return

        self.turn = 0
        self.sentences = {}
        self.started = True

        await interaction.response.send_message("📖 故事接龍開始！第一位玩家請輸入 `/story_write`", ephemeral=False)

    @nextcord.slash_command(name="story_write", description="寫下你的句子")
    async def story_write(self, interaction: Interaction, text: str = SlashOption(description="你的句子")):
        if not self.started:
            await interaction.response.send_message("故事尚未開始！", ephemeral=True)
            return

        uid = interaction.user.id
        expected_uid = self.players[self.turn]

        if uid != expected_uid:
            await interaction.response.send_message("還不是你的回合喔！", ephemeral=True)
            return

        self.sentences[uid] = text
        self.turn += 1

        if self.turn >= len(self.players):
            await interaction.response.send_message("📚 本輪結束！使用 `/story_end` 查看完整故事！", ephemeral=False)
            self.started = False
        else:
            next_user = f"<@{self.players[self.turn]}>"
            await interaction.response.send_message(f"下一位輪到 {next_user}", ephemeral=False)

    @nextcord.slash_command(name="story_end", description="結束故事接龍")
    async def story_end(self, interaction: Interaction):
        story_text = "📖 **故事接龍結算**\n\n"

        for pid in self.players:
            part = self.sentences.get(pid, "（未提供內容）")
            story_text += f"📘 <@{pid}>:{part}\n"  # 正確的 f-string 格式

        embed = nextcord.Embed(
            title="故事完成！",
            description=story_text,
            color=0xffcc66
        )

        await interaction.response.send_message(embed=embed, ephemeral=False)


# ============================================================
# 導出函式給主程式使用
# ============================================================

def setup(bot):
    bot.add_cog(TOD(bot))
    bot.add_cog(StoryCog(bot))

# 添加 !help 指令顯示所有指令
@bot.command()
async def help(ctx):
    help_text = """
    📘 **千惠 Bot 指令一覽**

    🎴 一般指令
    !ping — 檢查 bot 是否在線
    !megumin <訊息> — 讓千惠用惠惠語氣回覆你
    !draw — 今日運勢抽籤
    !遠征排行 — 查看遠征傷害排行榜

    🌸 故事接龍（Slash 指令）
    /story — 開啟故事接龍控制面板
    /story_add_player — 加入故事接龍
    /story_remove_player — 退出故事接龍
    /story_start — 開始接龍
    /story_write — 撰寫你的句子
    /story_prev — 查看上一句（僅輪到你）
    /story_end — 結算故事並查看完整內容

    🎲 真心話大冒險（Slash 指令）
    /tod — 開始真心話大冒險遊戲

    📝 生活化數據
    !report — 顯示今天的聊天統計數據
    !daily_report — 查看每日訊息統計

    """

    await ctx.send(help_text)

