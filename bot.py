```python
import discord
import json
import os
import re

from dotenv import load_dotenv


# ==================================================
# 환경 설정
# ==================================================

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")


# ==================================================
# 디스코드 설정
# ==================================================

intents = discord.Intents.default()

intents.members = True
intents.message_content = True


bot = discord.Client(
    intents=intents
)


# ==================================================
# 채널 / 역할 ID
# ==================================================

HEART_CHANNEL_ID = 1551099030409314384

GUIDE_CHANNEL_ID = 1556000267701330071

ROLE_ID = 1535737518824358179


# ==================================================
# 인증 데이터
# ==================================================

DATA_FILE = "auth_data.json"


if os.path.exists(DATA_FILE):

    try:

        with open(
            DATA_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            auth_data = json.load(f)

    except Exception:

        auth_data = {}

else:

    auth_data = {}


def save_data(data):

    with open(
        DATA_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=4
        )


# ==================================================
# 닉네임 형식
#
# 년생 롤 닉네임#태그 / 티어 / 주라인
# ==================================================

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

    match = NICKNAME_PATTERN.match(
        nickname.strip()
    )

    if not match:

        return None

    return match.groupdict()


def is_valid_nickname(nickname):

    return parse_nickname(nickname) is not None


# ==================================================
# 인증 안내 Embed
# ==================================================

async def send_guide_message():

    try:

        # ------------------------------
        # 채널 가져오기
        # ------------------------------

        channel = bot.get_channel(
            GUIDE_CHANNEL_ID
        )

        if channel is None:

            channel = await bot.fetch_channel(
                GUIDE_CHANNEL_ID
            )

        print(
            "🤍 인증안내 채널 확인 완료"
        )

        print(
            f"📌 채널: {channel.name}"
        )

        print(
            f"📌 채널 ID: {channel.id}"
        )


        # ------------------------------
        # 기존 봇 인증안내 Embed 삭제
        # ------------------------------

        async for message in channel.history(
            limit=50
        ):

            if message.author != bot.user:

                continue


            if not message.embeds:

                continue


            for old_embed in message.embeds:

                if (
                    old_embed.title
                    == "🤍 롤하자 인증 안내"
                ):

                    try:

                        await message.delete()

                        print(
                            "🗑️ 기존 인증안내 Embed 삭제 완료"
                        )

                    except Exception as e:

                        print(
                            "⚠️ 기존 인증안내 Embed 삭제 실패: "
                            f"{type(e).__name__}: {e}"
                        )

                    break


        # ------------------------------
        # 새 Embed
        # ------------------------------

        embed = discord.Embed(

            title="🤍 롤하자 인증 안내",

            description=(

                "① 닉네임 변경\n"

                "`년생 롤 닉네임#태그 / 티어 / 주라인`\n\n"

                "예시\n"

                "`00 억울합니다#제가던졌 / P3 / 서폿`\n"

                "`99 Faker#KR1 / D1 / 미드`\n"

                "`01 아무개#KR2 / U / 탑`\n\n"

                "② 하트 인증\n"

                "💙 하트 인증 채널에 인증샷을 올려주세요.\n\n"

                "닉네임 변경 + 인증샷 업로드 완료 시\n"

                "🏷️ `롤하자` 역할이 자동 지급됩니다."

            ),

            color=discord.Color.light_grey()

        )


        # ------------------------------
        # 실제 Embed 내용 로그
        # ------------------------------

        print(
            "📦 실제 전송할 Embed 내용:"
        )

        print(
            embed.description
        )


        # ------------------------------
        # Embed 전송
        # ------------------------------

        await channel.send(
            embed=embed
        )

        print(
            "✅ 새 인증안내 Embed 전송 완료"
        )


    except discord.Forbidden:

        print(
            "❌ 인증안내 채널에 메시지를 보낼 권한이 없습니다."
        )


    except Exception as e:

        print(
            "❌ 인증안내 Embed 전송 오류: "
            f"{type(e).__name__}: {e}"
        )


# ==================================================
# 역할 지급 확인
# ==================================================

async def check_and_give_role(member):

    print(
        "=" * 50
    )

    print(
        "🔎 역할 확인 시작"
    )

    print(
        f"👤 사용자: {member}"
    )

    print(
        f"📝 현재 닉네임: {member.nick}"
    )


    # ------------------------------
    # 하트 인증 확인
    # ------------------------------

    user_id = str(
        member.id
    )

    heart_verified = (
        auth_data
        .get(user_id, {})
        .get("heart", False)
    )

    print(
        f"💙 하트 인증: {heart_verified}"
    )


    # ------------------------------
    # 닉네임 확인
    # ------------------------------

    nickname_info = parse_nickname(
        member.nick
    )


    if nickname_info:

        print(
            "✅ 닉네임 형식: 정상"
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


    # ------------------------------
    # 하트 인증 X
    # ------------------------------

    if not heart_verified:

        print(
            "⏸️ 하트 인증이 없어 역할 지급 안 함"
        )

        return


    # ------------------------------
    # 닉네임 X
    # ------------------------------

    if nickname_info is None:

        print(
            "⏸️ 닉네임 형식이 맞지 않아 역할 지급 안 함"
        )

        return


    # ------------------------------
    # 역할 찾기
    # ------------------------------

    role = member.guild.get_role(
        ROLE_ID
    )


    if role is None:

        print(
            "❌ 롤하자 역할을 찾을 수 없습니다."
        )

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

        return


    # ------------------------------
    # 역할 지급
    # ------------------------------

    try:

        await member.add_roles(

            role,

            reason="롤하자 인증 완료"

        )

        print(
            "🎉 롤하자 역할 지급 완료!"
        )


    except discord.Forbidden:

        print(
            "❌ 역할 지급 실패: "
            "봇의 역할이 대상 역할보다 낮거나 "
            "권한이 없습니다."
        )


    except Exception as e:

        print(
            "❌ 역할 지급 오류: "
            f"{type(e).__name__}: {e}"
        )


# ==================================================
# 봇 준비 완료
# ==================================================

@bot.event
async def on_ready():

    print(
        "=" * 50
    )

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
        "🤍 인증안내 Embed 적용 완료"
    )

    print(
        "=" * 50
    )


    # ------------------------------
    # 인증안내 Embed 자동 등록
    # ------------------------------

    await send_guide_message()


# ==================================================
# 메시지 감지
# 하트 인증
# ==================================================

@bot.event
async def on_message(message):

    # 봇 메시지 무시
    if message.author.bot:

        return


    # 하트 인증 채널이 아니면 무시
    if (
        message.channel.id
        != HEART_CHANNEL_ID
    ):

        return


    # ------------------------------
    # 이미지 확인
    # ------------------------------

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


    # ------------------------------
    # 데이터 생성
    # ------------------------------

    user_id = str(
        message.author.id
    )


    if user_id not in auth_data:

        auth_data[user_id] = {}


    # ------------------------------
    # 하트 인증 완료
    # ------------------------------

    auth_data[user_id]["heart"] = True

    save_data(
        auth_data
    )


    print(
        f"💙 하트 인증 완료: "
        f"{message.author} "
        f"({message.author.id})"
    )


    # ------------------------------
    # 하트 + 닉네임 확인
    # ------------------------------

    if isinstance(
        message.author,
        discord.Member
    ):

        await check_and_give_role(
            message.author
        )


# ==================================================
# 닉네임 변경 감지
# ==================================================

@bot.event
async def on_member_update(
    before,
    after
):

    # 닉네임이 바뀌지 않았으면 무시
    if before.nick == after.nick:

        return


    print(
        "=" * 50
    )

    print(
        "🔄 닉네임 변경 감지"
    )

    print(
        f"👤 사용자: {after}"
    )

    print(
        f"📝 이전 닉네임: {before.nick}"
    )

    print(
        f"📝 변경 닉네임: {after.nick}"
    )


    # ------------------------------
    # 닉네임 형식 확인
    # ------------------------------

    nickname_info = parse_nickname(
        after.nick
    )


    # ------------------------------
    # 형식이 잘못된 경우
    # ------------------------------

    if nickname_info is None:

        try:

            await after.send(

                "❌ **닉네임 형식이 올바르지 않습니다.**\n\n"

                "롤하자 닉네임은 아래 형식으로 변경해주세요.\n\n"

                "`년생 롤 닉네임#태그 / 티어 / 주라인`\n\n"

                "예시:\n"

                "`00 억울합니다#제가던졌 / P3 / 서폿`\n"

                "`99 Faker#KR1 / D1 / 미드`\n"

                "`01 아무개#KR2 / U / 탑`\n\n"

                "티어:\n"

                "`U`, `I1~I4`, `B1~B4`, "
                "`S1~S4`, `G1~G4`, "
                "`P1~P4`, `E1~E4`, `D1~D4`\n\n"

                "마스터 이상:\n"

                "`M800`, `GM425`, `C1200`\n\n"

                "주라인:\n"

                "`탑 / 정글 / 미드 / 원딜 / 서폿 / 서포터`"

            )


            print(
                "📩 잘못된 닉네임 형식 DM 전송"
            )


        except discord.Forbidden:

            print(
                "⚠️ 사용자에게 DM을 보낼 수 없습니다."
            )


        except Exception as e:

            print(
                "⚠️ DM 전송 오류: "
                f"{type(e).__name__}: {e}"
            )


    else:

        print(
            "✅ 닉네임 형식: 정상"
        )


    # ------------------------------
    # 하트 + 닉네임 확인
    # ------------------------------

    await check_and_give_role(
        after
    )


# ==================================================
# 봇 실행
# ==================================================

if not TOKEN:

    print(
        "❌ DISCORD_TOKEN이 설정되지 않았습니다."
    )

else:

    print(
        "🚀 롤하자 봇 시작 중..."
    )

    bot.run(
        TOKEN
    )
```# 2026-10-05 update
