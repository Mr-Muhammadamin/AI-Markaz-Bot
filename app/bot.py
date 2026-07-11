import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from app.config import settings
from app.providers import get_provider, list_all, list_enabled
from app.storage import get_session

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

bot = Bot(
    token=settings.telegram_bot_token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()


def is_allowed(user_id: int) -> bool:
    if not settings.allowed_user_ids:
        return True
    return user_id in settings.allowed_user_ids


def agents_list_text() -> str:
    lines = ["<b>Mavjud AI agentlar:</b>"]
    for key in list_all():
        cfg = settings.providers[key]
        status = "✅ yoqilgan" if cfg.enabled else "⛔ API kaliti yo'q"
        lines.append(f"• <code>{key}</code> — {cfg.name} ({status}, model: {cfg.model})")
    lines.append("\nTanlash uchun: <code>/use provayder_nomi</code>")
    return "\n".join(lines)


@dp.message(Command("start"))
async def cmd_start(message: Message):
    if not is_allowed(message.from_user.id):
        await message.answer("⛔ Kechirasiz, sizga ushbu botdan foydalanishga ruxsat berilmagan.")
        return

    text = (
        "👋 <b>AI Markaz</b>ga xush kelibsiz!\n\n"
        "Bu bot orqali bitta joydan barcha AI agentlaringizga (ChatGPT, Claude, Gemini, "
        "DeepSeek, OpenRouter, Groq) buyruq bera olasiz.\n\n"
        f"{agents_list_text()}\n\n"
        "Boshqa buyruqlar uchun /help yozing."
    )
    await message.answer(text)


@dp.message(Command("help"))
async def cmd_help(message: Message):
    if not is_allowed(message.from_user.id):
        return
    text = (
        "<b>Buyruqlar:</b>\n"
        "/agents - mavjud agentlar ro'yxati\n"
        "/use <code><nomi></code> - agentni tanlash (masalan: <code>/use openai</code>)\n"
        "/broadcast <code><matn></code> - barcha yoqilgan agentlarga bir vaqtda xabar yuborish\n"
        "/reset - joriy suhbat tarixini tozalash\n\n"
        "Oddiy xabar yozsangiz, u joriy tanlangan agentga yuboriladi."
    )
    await message.answer(text)


@dp.message(Command("agents"))
async def cmd_agents(message: Message):
    if not is_allowed(message.from_user.id):
        return
    await message.answer(agents_list_text())


@dp.message(Command("use"))
async def cmd_use(message: Message, command: CommandObject):
    if not is_allowed(message.from_user.id):
        return

    key = (command.args or "").strip().lower()
    if not key:
        await message.answer("Iltimos, agent nomini kiriting. Masalan: <code>/use openai</code>\n\n" + agents_list_text())
        return

    if key not in list_all():
        await message.answer(f"⛔ Noma'lum agent: <code>{key}</code>\n\n" + agents_list_text())
        return

    if key not in list_enabled():
        await message.answer(
            f"⛔ <code>{key}</code> uchun API kaliti sozlanmagan. .env faylida kalitni kiriting."
        )
        return

    session = get_session(message.from_user.id)
    session.provider_key = key
    session.reset()
    await message.answer(f"✅ Faol agent o'zgartirildi: <b>{settings.providers[key].name}</b>")


@dp.message(Command("reset"))
async def cmd_reset(message: Message):
    if not is_allowed(message.from_user.id):
        return
    session = get_session(message.from_user.id)
    session.reset()
    await message.answer("🗑 Suhbat tarixi tozalandi.")


@dp.message(Command("broadcast"))
async def cmd_broadcast(message: Message, command: CommandObject):
    if not is_allowed(message.from_user.id):
        return

    text = (command.args or "").strip()
    if not text:
        await message.answer("Iltimos, yubormoqchi bo'lgan xabar matnini kiriting.\nMasalan: <code>/broadcast Salom, ahvolingiz qanday?</code>")
        return

    enabled = list_enabled()
    if not enabled:
        await message.answer("⛔ Hech qanday agent sozlanmagan. .env faylida API kalitlarini kiriting.")
        return

    await message.answer(f"⏳ {len(enabled)} ta agentga xabar yuborilmoqda...")

    async def ask_one(key: str):
        provider = get_provider(key)
        try:
            answer = await provider.ask([{"role": "user", "content": text}])
            return key, answer, None
        except Exception as e:
            return key, None, str(e)

    results = await asyncio.gather(*(ask_one(k) for k in enabled))

    for key, answer, error in results:
        name = settings.providers[key].name
        if error:
            await message.answer(f"❌ <b>{name}</b>:\n{error}")
        else:
            await message.answer(f"🤖 <b>{name}</b>:\n{answer}")


@dp.message(F.text)
async def handle_text(message: Message):
    if not is_allowed(message.from_user.id):
        await message.answer("⛔ Kechirasiz, sizga ushbu botdan foydalanishga ruxsat berilmagan.")
        return

    session = get_session(message.from_user.id)

    if not session.provider_key:
        enabled = list_enabled()
        if not enabled:
            await message.answer(
                "⛔ Hech qanday AI agent sozlanmagan. .env faylida kamida bitta API kalitini kiriting."
            )
            return
        session.provider_key = enabled[0]
        await message.answer(
            f"ℹ️ Faol agent avtomatik tanlandi: <b>{settings.providers[session.provider_key].name}</b>\n"
            "Boshqa agentni tanlash uchun /use buyrug'idan foydalaning."
        )

    provider = get_provider(session.provider_key)
    if provider is None:
        await message.answer("⛔ Tanlangan agent hozir mavjud emas. /agents orqali boshqasini tanlang.")
        return

    session.add_user_message(message.text)

    await bot.send_chat_action(message.chat.id, "typing")
    try:
        answer = await provider.ask(session.history)
        session.add_assistant_message(answer)
        await message.answer(answer)
    except Exception as e:
        logger.exception("Provider xatoligi")
        await message.answer(f"❌ Xatolik yuz berdi: {e}")


async def main():
    if not settings.telegram_bot_token:
        raise SystemExit("TELEGRAM_BOT_TOKEN .env faylida kiritilmagan!")

    enabled = list_enabled()
    if enabled:
        logger.info("Yoqilgan agentlar: %s", ", ".join(enabled))
    else:
        logger.warning("Hech qanday AI agent uchun API kaliti topilmadi. .env faylini tekshiring.")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())