# bot.py (نسخه نهایی با دکمه‌های بازگشت و منوی اصلی)

import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import CommandStart
from config import BOT_TOKEN
from database import init_db, get_available_times, create_reservation, get_reservation_by_code, delete_reservation_by_code, get_user_reservations
from keyboards import main_menu, specialty_menu, date_menu, time_inline_keyboard
from utils import generate_reservation_code, jalali_to_gregorian, gregorian_to_jalali

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

user_state = {}

# تابع کمکی برای بازگشت به منوی اصلی
async def go_to_main_menu(message: Message):
    user_state.pop(message.from_user.id, None)
    await message.answer("به منوی اصلی بازگشتید.", reply_markup=main_menu())

@router.message(CommandStart())
async def start_handler(message: Message):
    await go_to_main_menu(message)

@router.message(F.text == "🔹 رزرو وقت ویزیت")
async def reserve_visit(message: Message):
    user_id = message.from_user.id
    user_state[user_id] = {"step": "choose_specialty"}
    await message.answer("لطفاً تخصص مورد نظر خود را انتخاب کنید:", reply_markup=specialty_menu())

@router.message(F.text.in_({"عمومی", "ارتودنسی", "ایمپلنت", "لیزر"}))
async def specialty_selected(message: Message):
    user_id = message.from_user.id
    if user_state.get(user_id, {}).get("step") == "choose_specialty":
        user_state[user_id]["specialty"] = message.text
        user_state[user_id]["step"] = "choose_date"
        await message.answer("تاریخ مورد نظر خود را از لیست زیر انتخاب کنید:", reply_markup=date_menu())

@router.message(F.text.regexp(r"^\d{4}/\d{2}/\d{2}$"))
async def date_selected(message: Message):
    user_id = message.from_user.id
    if user_state.get(user_id, {}).get("step") == "choose_date":
        try:
            greg_date = jalali_to_gregorian(message.text)
            datetime.strptime(greg_date, "%Y-%m-%d")
            user_state[user_id]["date"] = greg_date
            available = await get_available_times(greg_date)
            if not available:
                await message.answer("متاسفانه در این تاریخ ساعت خالی وجود ندارد.", reply_markup=date_menu())
                return
            await message.answer("ساعت‌های خالی:", reply_markup=ReplyKeyboardRemove())
            await message.answer("لطفاً یکی از ساعات زیر را انتخاب کنید:",
                                 reply_markup=time_inline_keyboard(available, greg_date))
        except:
            await message.answer("تاریخ نامعتبر است.", reply_markup=date_menu())

# مدیریت callbackها
@router.callback_query(F.data == "back_to_date")
async def back_to_date(callback: CallbackQuery):
    await callback.message.answer("تاریخ مورد نظر خود را انتخاب کنید:", reply_markup=date_menu())
    await callback.answer()

@router.callback_query(F.data == "main_menu")
async def back_to_main_from_inline(callback: CallbackQuery):
    await go_to_main_menu(callback.message)
    await callback.answer()

@router.callback_query(F.data.startswith("select_time:"))
async def time_selected(callback: CallbackQuery):
    parts = callback.data.split(":", maxsplit=2)
    if len(parts) != 3:
        await callback.answer("خطا: داده نامعتبر است.", show_alert=True)
        return
    _, greg_date, time_slot = parts
    user_id = callback.from_user.id
    if user_state.get(user_id, {}).get("step") != "choose_date":
        await callback.answer("لطفاً دوباره از ابتدا شروع کنید.", show_alert=True)
        return
    user_state[user_id]["time"] = time_slot
    user_state[user_id]["step"] = "get_name"
    await callback.message.answer("لطفاً نام و نام خانوادگی خود را وارد کنید:")
    await callback.answer()

# مدیریت دکمه‌های متنی: «بازگشت» و «منوی اصلی»
@router.message(F.text.in_({"« بازگشت", "🏠 منوی اصلی"}))
async def handle_navigation(message: Message):
    if message.text == "« بازگشت":
        # سعی می‌کنیم به مرحله قبل برگردیم (ساده‌شده: همیشه به انتخاب تخصص)
        user_id = message.from_user.id
        current_step = user_state.get(user_id, {}).get("step")
        if current_step in ["choose_date", "get_name", "get_phone"]:
            user_state[user_id] = {"step": "choose_specialty"}
            await message.answer("لطفاً تخصص مورد نظر خود را انتخاب کنید:", reply_markup=specialty_menu())
        else:
            await go_to_main_menu(message)
    elif message.text == "🏠 منوی اصلی":
        await go_to_main_menu(message)

# مدیریت ورودی‌های متنی (نام، شماره، کد رزرو و ...)
@router.message()
async def handle_text_input(message: Message):
    user_id = message.from_user.id
    text = message.text.strip()
    step = user_state.get(user_id, {}).get("step")

    if step == "get_name":
        if not text:
            await message.answer("نام نمی‌تواند خالی باشد.")
            return
        user_state[user_id]["full_name"] = text
        user_state[user_id]["step"] = "get_phone"
        await message.answer("لطفاً شماره تماس خود را وارد کنید (مثال: 09123456789):")

    elif step == "get_phone":
        if not (text.isdigit() and len(text) >= 10 and text.startswith('09')):
            await message.answer("شماره موبایل معتبر وارد کنید (مثال: 09123456789):")
            return
        user_state[user_id]["phone"] = text
        data = user_state[user_id]
        code = generate_reservation_code()
        await create_reservation(user_id, data["full_name"], data["phone"], data["specialty"], data["date"], data["time"], code)
        jalali_date = gregorian_to_jalali(data["date"])
        await message.answer(
            f"✅ رزرو شما ثبت شد!\n\nنام: {data['full_name']}\nتخصص: {data['specialty']}\nتاریخ: {jalali_date}\nساعت: {data['time']}\nکد رزرو: `{code}`",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )
        user_state.pop(user_id, None)

    elif text == "🔹 لغو رزرو":
        await message.answer("کد رزرو خود را وارد کنید (مثال: LS-20250405-ABCD):")
    elif text == "🔹 مشاهده وقت‌های رزرو شده":
        reservations = await get_user_reservations(user_id)
        if not reservations:
            await message.answer("شما رزرو فعالی ندارید.")
        else:
            msg = "رزروهای شما:\n\n"
            for r in reservations:
                _, _, name, _, spec, g_date, time, code, _ = r
                msg += f"• {spec} | {gregorian_to_jalali(g_date)} | {time}\nکد: {code}\n\n"
            await message.answer(msg)
    elif text == "🔹 اطلاعات کلینیک":
        await message.answer(
            "📍 آدرس: تهران، ولیعصر، نرسیده به ونک، کوچه دندان، پلاک 15\n"
            "📞 تماس: 021-12345678\n"
            "🕒 ساعات کاری: شنبه تا چهارشنبه 9-17\n"
            "🗺️ [نقشه](https://maps.google.com/)",
            parse_mode="Markdown"
        )
    elif text.startswith("LS-") and len(text) > 12:
        if await delete_reservation_by_code(text):
            await message.answer("رزرو شما لغو شد. ✅")
        else:
            await message.answer("کد رزرو معتبر نیست.")
    else:
        # هر متن دیگری → منوی اصلی
        await go_to_main_menu(message)

dp.include_router(router)

async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())