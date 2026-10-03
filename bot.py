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


# ==============================
# 인증 데이터 불러오기
# ==============================

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception as e:
        print(f"⚠️ 데이터 불러오기 실패: {type(e).__name__}: {e}")
        return {}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


auth_data = load_data()


# ==============================
# 새 닉네임 형식
#
# 롤 닉네임#태그 / 티어 / 주라인
#
# 예:
# 뿌직#휴지 / P2 / 정글
# 아무개#KR1 / D1 / 미드
# 고수#KR2 / M800 / 탑
# ==============================

TIER_PATTERN = (
    r"(?:"
    r"[IBSGPED][1-4]"
    r"|M[1-9]\d{0,3}"
    r"|GM[1-9]\d{0,3}"
    r"|C[1-9]\d{0,3}"
    r")"
)

POSITION_PATTERN = (
    r"(?:탑|정글|미드|원딜|서폿|서포터)"
)

NICKNAME_PATTERN = re.compile(
    rf"^(?P<name>[^#/\n]+?)"
    rf"#(?P<tag>[^/\n]+?)"
    rf"\s*/\s*"
    rf"(?P<tier>{TIER_PATTERN})"
    rf"\s*/\s*"
    rf"(?P<position>{POSITION_PATTERN})$"
)


def parse_nickname(nickname):
    if not nickname:
        return None

    match = NICKNAME_PATTERN.fullmatch(nickname.strip())

    if match is None:
        return None

    return {
        "name": match.group("name").strip(),
        "tag": match.group("tag").strip(),
        "tier": match.group("tier").strip(),
        "position": match.group("position").strip(),
    }


def is_valid_nickname(nickname):
    return parse_nickname(nickname) is not None


# ==============================
# 하트 + 닉네임 인증 확인
# ==============================

async def check_and_give_role(member):
    user_id = str(member.id)

    print("=" * 50)
    print(f"🔎 역할 확인 시작")
    print(f"👤 사용자: {member}")
    print(f"📝 현재 닉네임: {member.nick}")

    # 하트 인증 여부
    heart_verified = auth_data.get(user_id, {}).get("heart", False)

    print(f"❤️ 하트 인증: {heart_verified}")

    # 새 닉네임 형식 확인
    nickname_info = parse_nickname(member.nick)

    if nickname_info:
        print("✅ 닉네임 형식: 정상")
        print(f"🎮 롤 닉네임: {nickname_info['name']}")
        print(f"🏷️ 태그: {nickname_info['tag']}")
        print(f"🏆 티어: {nickname_info['tier']}")
        print(f"🎯 주라인: {nickname_info['position']}")
    else:
        print("❌ 닉네임 형식: 불일치")

    # 하트 인증이 없으면 종료
    if not heart_verified:
        print("❌ 역할 지급 중단: 하트 인증 안 됨")
        print("=" * 50)
        return

    # 닉네임 형식이 틀리면 종료
    if nickname_info is None:
        print("❌ 역할 지급 중단: 닉네임 형식 불일치")
        print("=" * 50)
        return

    # 역할 찾기
    role = member.guild.get_role(ROLE_ID)

    if role is None:
        print(f"❌ 역할을 찾을 수 없습니다.")
        print(f"역할 ID: {ROLE_ID}")
        print("=" * 50)
        return

    print(f"🏷️ 찾은 역할: {role.name}")

    # 이미 역할이 있으면 종료
    if role in member.roles:
        print("ℹ️ 이미 롤하자 역할이 있습니다.")
        print("=" * 50)
        return

    # 역할 지급
    try:
        await member.add_roles(
            role,
            reason="롤하자 하트 인증 + 닉네임 인증 완료"
        )

        print(f"✅ 롤하자 역할 지급 완료: {member} ({member.id})")

    except discord.Forbidden:
        print("❌ 역할 지급 실패")
        print("봇의 역할이 대상 역할보다 낮거나 권한이 없습니다.")

    except Exception as e:
        print(
            f"❌ 역할 지급 중 오류: "
            f"{type(e).__name__}: {e}"
        )

    print("=" * 50)


# ==============================
# 봇 로그인 완료
# ==============================

@bot.event
async def on_ready():
    print("=" * 50)
    print(f"로그인 성공: {bot.user}")
    print("🔥 롤하자 봇 실행 중")
    print("📝 새 닉네임 형식 적용 완료")
    print("=" * 50)


# ==============================
# 하트 인증
# ==============================

@bot.event
async def on_message(message):

    # 봇 메시지 무시
    if message.author.bot:
        return

    # 하트 인증 채널이 아니면 무시
    if message.channel.id != HEART_CHANNEL_ID:
        return

    # 이미지 첨부 여부 확인
    has_image = False

    for attachment in message.attachments:

        if attachment.content_type:

            if attachment.content_type.startswith("image/"):
                has_image = True
                break

    # 이미지가 없으면 무시
    if not has_image:
        return

    user_id = str(message.author.id)

    # 데이터 생성
    if user_id not in auth_data:
        auth_data[user_id] = {}

    # 하트 인증 완료
    auth_data[user_id]["heart"] = True

    save_data(auth_data)

    print(
        f"❤️ 하트 인증 완료: "
        f"{message.author} ({message.author.id})"
    )

    # 닉네임 + 하트 둘 다 확인
    if isinstance(message.author, discord.Member):
        await check_and_give_role(message.author)


# ==============================
# 닉네임 변경 감지
# ==============================

@bot.event
async def on_member_update(before, after):

    # 닉네임이 바뀐 게 아니면 무시
    if before.nick == after.nick:
        return

    print("=" * 50)
    print("📝 닉네임 변경 감지")
    print(f"이전: {before.nick}")
    print(f"현재: {after.nick}")
    print("=" * 50)

    # 새 닉네임 형식 + 하트 인증 확인
    await check_and_give_role(after)


# ==============================
# 봇 시작
# ==============================

print("🚀 롤하자 봇 시작 중...")

bot.run(TOKEN)
