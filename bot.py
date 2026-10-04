import discord
import json
import os
import re

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = discord.Client(intents=intents)

HEART_CHANNEL_ID = 1551099030409314384
GUIDE_CHANNEL_ID = 1556000267701330071
ROLE_ID = 1535737518824358179

DATA_FILE = "auth_data.json"


# =========================
# 인증 데이터 불러오기
# =========================

if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            auth_data = json.load(f)
    except Exception:
        auth_data = {}
else:
    auth_data = {}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# =========================
# 닉네임 형식
# =========================

TIER_PATTERN = (
    r"(?:"
    r"U"
    r"|[IBSGPED][1-4]"
    r"|GM[1-9]\d{0,3}"
    r"|M[1-9]\d{0,3}"
    r"|C[1-9]\d{0,3}"
    r")"
)

POSITION_PATTERN = r"(?:탑|정글|미드|원딜|서폿|서포터)"

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


# =========================
# 인증 안내 Embed
# =========================

async def send_guide_message():
    try:
        channel = bot.get_channel(GUIDE_CHANNEL_ID)

        if channel is None:
            channel = await bot.fetch_channel(GUIDE_CHANNEL_ID)

        print("🤍 인증안내 채널 확인 완료")
        print(f"📌 채널: {channel.name}")
        print(f"📌 채널 ID: {channel.id}")

        # ---------------------------------
        # 봇이 기존에 보낸 Embed 전부 삭제
        # ---------------------------------

        deleted_count = 0

        async for message in channel.history(limit=100):
            if message.author != bot.user:
                continue

            if not message.embeds:
                continue

            try:
                await message.delete()
                deleted_count += 1
            except Exception as e:
                print(
                    f"⚠️ 기존 Embed 삭제 실패 "
                    f"({type(e).__name__}): {e}"
                )

        print(f"🗑️ 기존 봇 Embed {deleted_count}개 삭제 완료")

        # ---------------------------------
        # 새로운 인증 안내문
        # ---------------------------------

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

        print("📦 새 인증안내 Embed 내용:")
        print(embed.description)

        await channel.send(embed=embed)

        print("✅ 새 인증안내 Embed 전송 완료")

    except Exception as e:
        print(
            f"❌ 인증안내 Embed 처리 중 오류 "
            f"({type(e).__name__}): {e}"
        )


# =========================
# 역할 지급
# =========================

async def check_and_give_role(member):
    user_id = str(member.id)

    data = auth_data.get(user_id)

    if not data:
        return

    # 하트 인증이 없으면 지급하지 않음
    if not data.get("heart", False):
        return

    # 닉네임 확인
    nickname = member.nick or member.name

    if not NICKNAME_PATTERN.fullmatch(nickname):
        return

    # 이미 역할이 있으면 아무것도 하지 않음
    role = member.guild.get_role(ROLE_ID)

    if role is None:
        print("❌ 롤하자 역할을 찾을 수 없습니다.")
        return

    if role in member.roles:
        return

    try:
        await member.add_roles(role)
        print(
            f"🏷️ 롤하자 역할 지급: "
            f"{member} / {nickname}"
        )
    except Exception as e:
        print(
            f"❌ 역할 지급 실패 "
            f"({type(e).__name__}): {e}"
        )


# =========================
# 봇 시작
# =========================

@bot.event
async def on_ready():
    print("=" * 50)
    print(f"로그인 성공: {bot.user}")
    print("🔥 롤하자 봇 실행 중")
    print("📝 새 닉네임 형식 적용 완료")
    print("🤍 인증안내 Embed 적용 완료")
    print("=" * 50)

    await send_guide_message()


# =========================
# 메시지 감지
# =========================

@bot.event
async def on_message(message):

    # 봇 자신의 메시지는 무시
    if message.author == bot.user:
        return

    # 하트 인증 채널
    if message.channel.id == HEART_CHANNEL_ID:

        # 이미지가 있는 경우
        has_image = False

        for attachment in message.attachments:
            content_type = attachment.content_type or ""

            if content_type.startswith("image/"):
                has_image = True
                break

            filename = attachment.filename.lower()

            if filename.endswith(
                (".png", ".jpg", ".jpeg", ".gif", ".webp")
            ):
                has_image = True
                break

        if has_image:

            user_id = str(message.author.id)

            if user_id not in auth_data:
                auth_data[user_id] = {}

            auth_data[user_id]["heart"] = True

            save_data(auth_data)

            print(
                f"💙 하트 인증 완료: "
                f"{message.author}"
            )

            await check_and_give_role(message.author)


# =========================
# 닉네임 변경 감지
# =========================

@bot.event
async def on_member_update(before, after):

    # 닉네임이 실제로 변경된 경우만 처리
    if before.nick == after.nick:
        return

    nickname = after.nick or after.name

    print(
        f"📝 닉네임 변경 감지: "
        f"{before.nick} → {nickname}"
    )

    # 올바른 형식인지 확인
    if not NICKNAME_PATTERN.fullmatch(nickname):

        try:
            await after.send(
                "❌ **롤하자 닉네임 형식이 올바르지 않습니다.**\n\n"
                "아래 형식으로 변경해주세요.\n"
                "`년생 롤 닉네임#태그 / 티어 / 주라인`\n\n"
                "예시\n"
                "`00 억울합니다#제가던졌 / P3 / 서폿`\n"
                "`99 Faker#KR1 / D1 / 미드`\n"
                "`01 아무개#KR2 / U / 탑`\n\n"
                "※ 롤 닉네임과 #태그에는 띄어쓰기가 가능합니다."
            )

            print(
                f"⚠️ 잘못된 닉네임 형식 안내 DM 전송: "
                f"{after}"
            )

        except Exception as e:
            print(
                f"⚠️ 닉네임 안내 DM 실패 "
                f"({type(e).__name__}): {e}"
            )

        return

    print(
        f"✅ 올바른 닉네임 형식: "
        f"{after} / {nickname}"
    )

    await check_and_give_role(after)


# =========================
# 봇 실행
# =========================

print("🚀 롤하자 봇 시작 중...")

bot.run(TOKEN)
# Railway deployment sync
