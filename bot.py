import os
import re
import json

import discord
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

# ==============================
# 채널 / 역할 ID
# ==============================

# 💙 하트 인증 채널
HEART_CHANNEL_ID = 1551099030409314384

# 🤍 인증안내 채널
GUIDE_CHANNEL_ID = 1556000267701330071

# 🏷️ 롤하자 역할
ROLE_ID = 1535737518824358179

# 인증 데이터 파일
DATA_FILE = "auth_data.json"


# ==============================
# 디스코드 설정
# ==============================

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = discord.Client(intents=intents)


# ==============================
# 인증 데이터
# ==============================

def load_data():

    if not os.path.exists(DATA_FILE):
        return {}

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception as e:
        print(
            f"⚠️ 데이터 불러오기 실패: "
            f"{type(e).__name__}: {e}"
        )

        return {}


def save_data(data):

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=4
        )


auth_data = load_data()


# ==============================
# 닉네임 형식
#
# 최종 형식
#
# 00 억울합니다#제가던졌 / P3 / 서폿
# 99 Faker#KR1 / D1 / 미드
# 01 아무개#KR2 / U / 탑
# ==============================

TIER_PATTERN = (
    r"(?:"
    r"U"
    r"|[IBSGPED][1-4]"
    r"|GM[1-9]\d{0,3}"
    r"|M[1-9]\d{0,3}"
    r"|C[1-9]\d{0,3}"
    r")"
)

POSITION_PATTERN = (
    r"(?:탑|정글|미드|원딜|서폿|서포터)"
)

NICKNAME_PATTERN = re.compile(
    rf"^(?P<year>\d{{2}})"
    rf"\s+"
    rf"(?P<name>[^#/\n]+?)"
    rf"#(?P<tag>[^/\n]+?)"
    rf"\s*/\s*"
    rf"(?P<tier>{TIER_PATTERN})"
    rf"\s*/\s*"
    rf"(?P<position>{POSITION_PATTERN})$"
)


def parse_nickname(nickname):

    if not nickname:
        return None

    match = NICKNAME_PATTERN.fullmatch(
        nickname.strip()
    )

    if match is None:
        return None

    return {
        "year": match.group("year").strip(),
        "name": match.group("name").strip(),
        "tag": match.group("tag").strip(),
        "tier": match.group("tier").strip(),
        "position": match.group("position").strip(),
    }


def is_valid_nickname(nickname):

    return parse_nickname(nickname) is not None


# ==============================
# 🤍 인증안내 Embed
# ==============================

async def send_guide_message():

    channel = bot.get_channel(
        GUIDE_CHANNEL_ID
    )

    if channel is None:

        print(
            f"❌ 인증안내 채널을 찾을 수 없습니다."
            f" 채널 ID: {GUIDE_CHANNEL_ID}"
        )

        return

    try:

        # ==============================
        # 새 인증안내 Embed 내용
        # ==============================

        embed = discord.Embed(
            title="🤍 롤하자 인증 안내",
            description=(
                "**① 닉네임 변경**\n"
                "`년생 롤 닉네임#태그 / 티어 / 주라인`\n\n"

                "**예시**\n"
                "`00 억울합니다#제가던졌 / P3 / 서폿`\n"
                "`99 Faker#KR1 / D1 / 미드`\n"
                "`01 아무개#KR2 / U / 탑`\n\n"

                "**② 하트 인증**\n"
                "💙 하트 인증 채널에 인증샷을 올려주세요.\n\n"

                "**닉네임 변경 + 인증샷 업로드 완료 시**\n"
                "🏷️ `롤하자` 역할이 자동 지급됩니다."
            ),
            color=discord.Color.light_grey()
        )

        # ==============================
        # 기존 안내 Embed 찾기
        # ==============================

        old_message = None

        async for message in channel.history(
            limit=30
        ):

            if (
                message.author == bot.user
                and message.embeds
                and message.embeds[0].title
                == "🤍 롤하자 인증 안내"
            ):

                old_message = message
                break

        # ==============================
        # 기존 Embed가 있으면 수정
        # ==============================

        if old_message is not None:

            await old_message.edit(
                embed=embed
            )

            print(
                "✅ 기존 인증안내 Embed 업데이트 완료"
            )

            return

        # ==============================
        # 기존 Embed가 없으면 새로 전송
        # ==============================

        await channel.send(
            embed=embed
        )

        print(
            "✅ 새 인증안내 Embed 전송 완료"
        )

    except discord.Forbidden:

        print(
            "❌ 인증안내 채널에 "
            "메시지를 보낼 권한이 없습니다."
        )

    except Exception as e:

        print(
            f"❌ 인증안내 Embed 처리 오류: "
            f"{type(e).__name__}: {e}"
        )


# ==============================
# 역할 지급 확인
# ==============================

async def check_and_give_role(member):

    user_id = str(member.id)

    print("=" * 50)

    print(
        "🔎 역할 확인 시작"
    )

    print(
        f"👤 사용자: {member}"
    )

    print(
        f"📝 현재 닉네임: {member.nick}"
    )

    # ==============================
    # 하트 인증 확인
    # ==============================

    heart_verified = (
        auth_data
        .get(user_id, {})
        .get("heart", False)
    )

    print(
        f"💙 하트 인증: {heart_verified}"
    )

    # ==============================
    # 닉네임 확인
    # ==============================

    nickname_info = parse_nickname(
        member.nick
    )

    if nickname_info:

        print(
            "✅ 닉네임 형식: 정상"
        )

        print(
            f"🎂 년생: "
            f"{nickname_info['year']}"
        )

        print(
            f"🎮 롤 닉네임: "
            f"{nickname_info['name']}"
        )

        print(
            f"🏷️ 태그: "
            f"{nickname_info['tag']}"
        )

        print(
            f"🏆 티어: "
            f"{nickname_info['tier']}"
        )

        print(
            f"🎯 주라인: "
            f"{nickname_info['position']}"
        )

    else:

        print(
            "❌ 닉네임 형식: 불일치"
        )

    # ==============================
    # 하트 인증이 없으면 종료
    # ==============================

    if not heart_verified:

        print(
            "❌ 역할 지급 중단: "
            "하트 인증 안 됨"
        )

        print("=" * 50)

        return

    # ==============================
    # 닉네임 형식이 틀리면 종료
    # ==============================

    if nickname_info is None:

        print(
            "❌ 역할 지급 중단: "
            "닉네임 형식 불일치"
        )

        print("=" * 50)

        return

    # ==============================
    # 역할 찾기
    # ==============================

    role = member.guild.get_role(
        ROLE_ID
    )

    if role is None:

        print(
            "❌ 역할을 찾을 수 없습니다."
        )

        print(
            f"역할 ID: {ROLE_ID}"
        )

        print("=" * 50)

        return

    print(
        f"🏷️ 찾은 역할: {role.name}"
    )

    # ==============================
    # 이미 역할이 있으면 종료
    #
    # 중요:
    # 역할 제거 기능은 없음.
    # ==============================

    if role in member.roles:

        print(
            "ℹ️ 이미 롤하자 역할이 있습니다."
        )

        print("=" * 50)

        return

    # ==============================
    # 역할 지급
    # ==============================

    try:

        await member.add_roles(
            role,
            reason=(
                "롤하자 하트 인증 + "
                "닉네임 인증 완료"
            )
        )

        print(
            f"✅ 롤하자 역할 지급 완료: "
            f"{member} ({member.id})"
        )

    except discord.Forbidden:

        print(
            "❌ 역할 지급 실패: "
            "봇의 역할이 대상 역할보다 낮거나 "
            "권한이 없습니다."
        )

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

    print(
        f"로그인 성공: {bot.user}"
    )

    print(
        "🔥 롤하자 봇 실행 중"
    )

    print(
        "📝 최종 닉네임 형식 적용 완료"
    )

    print(
        "💙 하트 인증 적용 완료"
    )

    print(
        "🤍 인증안내 Embed 적용 완료"
    )

    print("=" * 50)

    await send_guide_message()


# ==============================
# 💙 하트 인증
# ==============================

@bot.event
async def on_message(message):

    if message.author.bot:
        return

    if message.channel.id != HEART_CHANNEL_ID:
        return

    # ==============================
    # 이미지 확인
    # ==============================

    has_image = False

    for attachment in message.attachments:

        if attachment.content_type:

            if attachment.content_type.startswith(
                "image/"
            ):

                has_image = True
                break

    if not has_image:
        return

    user_id = str(
        message.author.id
    )

    # ==============================
    # 데이터 생성
    # ==============================

    if user_id not in auth_data:

        auth_data[user_id] = {}

    # ==============================
    # 하트 인증 완료
    # ==============================

    auth_data[user_id]["heart"] = True

    save_data(auth_data)

    print(
        f"💙 하트 인증 완료: "
        f"{message.author} "
        f"({message.author.id})"
    )

    # ==============================
    # 하트 + 닉네임 확인
    # ==============================

    if isinstance(
        message.author,
        discord.Member
    ):

        await check_and_give_role(
            message.author
        )


# ==============================
# 닉네임 변경 감지
# ==============================

@bot.event
async def on_member_update(
    before,
    after
):

    if before.nick == after.nick:
        return

    print("=" * 50)

    print(
        "📝 닉네임 변경 감지"
    )

    print(
        f"이전: {before.nick}"
    )

    print(
        f"현재: {after.nick}"
    )

    print("=" * 50)

    # ==============================
    # 닉네임 형식 확인
    # ==============================

    nickname_info = parse_nickname(
        after.nick
    )

    # ==============================
    # 잘못된 형식이면 DM 안내
    # ==============================

    if nickname_info is None:

        try:

            await after.send(
                "❌ **닉네임 형식이 올바르지 않습니다.**\n\n"
                "롤하자 닉네임은 아래 형식으로 변경해주세요.\n\n"
                "`년생 롤 닉네임#태그 / 티어 / 주라인`\n\n"

                "**예시**\n"
                "`00 억울합니다#제가던졌 / P3 / 서폿`\n"
                "`99 Faker#KR1 / D1 / 미드`\n"
                "`01 아무개#KR2 / U / 탑`\n\n"

                "**티어 형식**\n"
                "`U` = 언랭\n"
                "`I1~I4` = 아이언\n"
                "`B1~B4` = 브론즈\n"
                "`S1~S4` = 실버\n"
                "`G1~G4` = 골드\n"
                "`P1~P4` = 플래티넘\n"
                "`E1~E4` = 에메랄드\n"
                "`D1~D4` = 다이아\n"
                "`M + LP` = 마스터\n"
                "`GM + LP` = 그랜드마스터\n"
                "`C + LP` = 챌린저"
            )

            print(
                "📩 잘못된 닉네임 형식 DM 전송"
            )

        except discord.Forbidden:

            print(
                "ℹ️ DM을 보낼 수 없습니다."
            )

        except Exception as e:

            print(
                f"⚠️ DM 전송 오류: "
                f"{type(e).__name__}: {e}"
            )

    # ==============================
    # 하트 + 닉네임 확인
    # ==============================

    await check_and_give_role(
        after
    )


# ==============================
# 봇 시작
# ==============================

print(
    "🚀 롤하자 봇 시작 중..."
)

bot.run(TOKEN)
