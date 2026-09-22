import os
import re
import json

import discord
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

HEART_CHANNEL_ID = 1551099030409314384
ROLE_ID = 1535737518824358179
DATA_FILE = "auth_data.json"

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = discord.Client(intents=intents)


def load_data():
    if not os.path.exists(DATA_FILE):
        return {}

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


auth_data = load_data()


NICKNAME_PATTERN = re.compile(
    r"^(?P<birth>\d{2})\s+"
    r"(?P<name>[^#\n]+?)"
    r"#(?P<tag>.+?)\s+"
    r"(?P<tier>GM|U|I|B|S|G|P|E|D|M|C)$"
)


def is_valid_nickname(nickname):
    if not nickname:
        return False

    return NICKNAME_PATTERN.fullmatch(nickname) is not None


async def check_and_give_role(member):
    user_id = str(member.id)

    print(f"🔎 역할 확인 시작: {member} / 닉네임: {member.nick}")

    heart_verified = auth_data.get(user_id, {}).get("heart", False)
    print(f"❤️ 하트 인증: {heart_verified}")

    nickname_valid = is_valid_nickname(member.nick)
    print(f"📝 닉네임 형식: {nickname_valid}")

    if not heart_verified:
        print("❌ 역할 지급 중단: 하트 인증 안 됨")
        return

    if not nickname_valid:
        print("❌ 역할 지급 중단: 닉네임 형식 불일치")
        return

    role = member.guild.get_role(ROLE_ID)

    if role is None:
        print(f"❌ 역할을 찾을 수 없습니다. 역할 ID: {ROLE_ID}")
        return

    print(f"🏷️ 찾은 역할: {role.name}")

    if role in member.roles:
        print("ℹ️ 이미 롤하자 역할이 있습니다.")
        return

    try:
        await member.add_roles(
            role,
            reason="롤하자 인증 완료"
        )
        print(f"✅ 롤하자 역할 지급 완료: {member} ({member.id})")

    except discord.Forbidden:
        print("❌ 역할 지급 실패: 봇의 역할이 대상 역할보다 낮거나 권한이 없습니다.")

    except Exception as e:
        print(f"❌ 역할 지급 중 오류: {type(e).__name__}: {e}")


@bot.event
async def on_ready():
    print("=" * 50)
    print(f"로그인 성공: {bot.user}")
    print("🔥 수정된 bot.py 실행 중")
    print("=" * 50)


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id != HEART_CHANNEL_ID:
        return

    has_image = False

    for attachment in message.attachments:
        if attachment.content_type:
            if attachment.content_type.startswith("image/"):
                has_image = True
                break

    if not has_image:
        return

    user_id = str(message.author.id)

    if user_id not in auth_data:
        auth_data[user_id] = {}

    auth_data[user_id]["heart"] = True
    save_data(auth_data)

    print(f"❤️ 하트 인증 완료: {message.author} ({message.author.id})")

    if isinstance(message.author, discord.Member):
        await check_and_give_role(message.author)


@bot.event
async def on_member_update(before, after):
    if before.nick == after.nick:
        return

    print("=" * 50)
    print("📝 닉네임 변경 감지")
    print(f"이전: {before.nick}")
    print(f"현재: {after.nick}")
    print("=" * 50)

    await check_and_give_role(after)


print("🚀 롤하자 봇 시작 중...")

bot.run(TOKEN)
