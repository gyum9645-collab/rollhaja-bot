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

# ❤️ 하트 인증 채널
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
# 인증 데이터 불러오기
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

    match = NICKNAME_PATTERN.fullmatch(
        nickname.strip()
    )

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
# 인증안내 메시지
# ==============================

GUIDE_MESSAGE = """🤍 **롤하자 인증 안내**

롤하자에 처음 오셨다면 아래 두 가지를 완료해주세요!

━━━━━━━━━━━━━━━━━━━━

**① 닉네임 변경**

디스코드 닉네임을 아래 형식으로 변경해주세요.

`롤 닉네임#태그 / 티어 / 주라인`

**예시**

`뿌직#휴지 / P2 / 정글`
`아무개#KR1 / D1 / 미드`
`고수#KR2 / M800 / 탑`

━━━━━━━━━━━━━━━━━━━━

**🏆 티어 작성 방법**

아이언 → `I1 ~ I4`

브론즈 → `B1 ~ B4`

실버 → `S1 ~ S4`

골드 → `G1 ~ G4`

플래티넘 → `P1 ~ P4`

에메랄드 → `E1 ~ E4`

다이아 → `D1 ~ D4`

마스터 → `M + LP`
예) `M78` / `M800`

그랜드마스터 → `GM + LP`
예) `GM425`

챌린저 → `C + LP`
예) `C1200`

━━━━━━━━━━━━━━━━━━━━

**🎯 주라인**

`탑 / 정글 / 미드 / 원딜 / 서폿`

━━━━━━━━━━━━━━━━━━━━

**② 하트 인증**

닉네임을 변경한 뒤

❤️ **하트 인증 채널에 인증샷을 올려주세요.**

━━━━━━━━━━━━━━━━━━━━

**✅ 인증 완료 조건**

**닉네임 형식 + 하트 인증**

두 가지가 모두 완료되면 봇이 자동으로

🏷️ **「롤하자」 역할을 지급합니다.**

━━━━━━━━━━━━━━━━━━━━

⚠️ 닉네임 형식이 맞지 않으면 역할이 지급되지 않습니다.

예시:

`뿌직#휴지 / P2 / 정글`

이 형식 그대로 작성해주세요! 💙
"""


# ==============================
# 인증안내 메시지 자동 등록
# ==============================

async def send_guide_message():

    channel = bot.get_channel(GUIDE_CHANNEL_ID)

    if channel is None:

        print(
            f"❌ 인증안내 채널을 찾을 수 없습니다."
            f" 채널 ID: {GUIDE_CHANNEL_ID}"
        )

        return

    try:

        # 최근 메시지 확인
        async for message in channel.history(limit=20):

            # 봇이 이미 안내문을 올려놓았다면
            # 다시 올리지 않음
            if (
                message.author == bot.user
                and "🤍 **롤하자 인증 안내**" in message.content
            ):

                print("ℹ️ 인증안내 메시지가 이미 있습니다.")
                return

        # 안내문 전송
        await channel.send(GUIDE_MESSAGE)

        print("✅ 인증안내 메시지 전송 완료")

    except discord.Forbidden:

        print(
            "❌ 인증안내 채널에 메시지를 보낼 권한이 없습니다."
        )

    except Exception as e:

        print(
            f"❌ 인증안내 메시지 전송 오류: "
            f"{type(e).__name__}: {e}"
        )


# ==============================
# 역할 지급 확인
# ==============================

async def check_and_give_role(member):

    user_id = str(member.id)

    print("=" * 50)

    print("🔎 역할 확인 시작")
    print(f"👤 사용자: {member}")
    print(f"📝 현재 닉네임: {member.nick}")

    # ------------------------------
    # 하트 인증 확인
    # ------------------------------

    heart_verified = (
        auth_data
        .get(user_id, {})
        .get("heart", False)
    )

    print(
        f"❤️ 하트 인증: {heart_verified}"
    )

    # ------------------------------
    # 닉네임 확인
    # ------------------------------

    nickname_info = parse_nickname(
        member.nick
    )

    if nickname_info:

        print("✅ 닉네임 형식: 정상")

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

        print("❌ 닉네임 형식: 불일치")

    # ------------------------------
    # 하트 인증 X
    # ------------------------------

    if not heart_verified:

        print(
            "❌ 역할 지급 중단: "
            "하트 인증 안 됨"
        )

        print("=" * 50)

        return

    # ------------------------------
    # 닉네임 X
    # ------------------------------

    if nickname_info is None:

        print(
            "❌ 역할 지급 중단: "
            "닉네임 형식 불일치"
        )

        print("=" * 50)

        return

    # ------------------------------
    # 역할 찾기
    # ------------------------------

    role = member.guild.get_role(
        ROLE_ID
    )

    if role is None:

        print(
            f"❌ 역할을 찾을 수 없습니다."
        )

        print(
            f"역할 ID: {ROLE_ID}"
        )

        print("=" * 50)

        return

    print(
        f"🏷️ 찾은 역할: {role.name}"
    )

    # ------------------------------
    # 이미 역할이 있으면 종료
    # ------------------------------

    if role in member.roles:

        print(
            "ℹ️ 이미 롤하자 역할이 있습니다."
        )

        print("=" * 50)

        return

    # ------------------------------
    # 역할 지급
    # ------------------------------

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
            "❌ 역할 지급 실패"
        )

        print(
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
        "📝 새 닉네임 형식 적용 완료"
    )

    print(
        "🤍 인증안내 기능 적용 완료"
    )

    print("=" * 50)

    # 인증안내 메시지 확인 / 등록
    await send_guide_message()


# ==============================
# 메시지 감지
# ==============================

@bot.event
async def on_message(message):

    # 봇 메시지 무시
    if message.author.bot:
        return

    # ------------------------------
    # 하트 인증 채널
    # ------------------------------

    if message.channel.id == HEART_CHANNEL_ID:

        has_image = False

        for attachment in message.attachments:

            if attachment.content_type:

                if attachment.content_type.startswith(
                    "image/"
                ):

                    has_image = True
                    break

        # 이미지가 없으면 종료
        if not has_image:
            return

        user_id = str(
            message.author.id
        )

        # 데이터 생성
        if user_id not in auth_data:

            auth_data[user_id] = {}

        # 하트 인증 완료
        auth_data[user_id]["heart"] = True

        save_data(auth_data)

        print(
            f"❤️ 하트 인증 완료: "
            f"{message.author} "
            f"({message.author.id})"
        )

        # 하트 + 닉네임 확인
        if isinstance(
            message.author,
            discord.Member
        ):

            await check_and_give_role(
                message.author
            )

        return


# ==============================
# 닉네임 변경 감지
# ==============================

@bot.event
async def on_member_update(
    before,
    after
):

    # 닉네임이 바뀐 게 아니면 무시
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

    # 닉네임 형식 확인
    nickname_info = parse_nickname(
        after.nick
    )

    # 형식이 잘못된 경우
    if nickname_info is None:

        try:

            await after.send(
                "❌ **닉네임 형식이 올바르지 않습니다.**\n\n"
                "롤하자 닉네임은 아래 형식으로 변경해주세요.\n\n"
                "`롤 닉네임#태그 / 티어 / 주라인`\n\n"
                "예시:\n"
                "`뿌직#휴지 / P2 / 정글`\n"
                "`아무개#KR1 / D1 / 미드`\n"
                "`고수#KR2 / M800 / 탑`\n\n"
                "🏆 티어는 `I1~I4`, `B1~B4`, "
                "`S1~S4`, `G1~G4`, `P1~P4`, "
                "`E1~E4`, `D1~D4` 형식입니다.\n"
                "마스터 이상은 `M800`, `GM425`, "
                "`C1200`처럼 LP를 입력해주세요."
            )

            print(
                "📩 잘못된 닉네임 형식 안내 DM 전송"
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

    # 하트 인증 + 역할 확인
    await check_and_give_role(after)


# ==============================
# 봇 시작
# ==============================

print(
    "🚀 롤하자 봇 시작 중..."
)

bot.run(TOKEN)
