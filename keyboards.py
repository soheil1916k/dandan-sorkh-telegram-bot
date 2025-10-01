# keyboards.py

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
from utils import get_next_7_days, gregorian_to_jalali

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔹 رزرو وقت ویزیت")],
            [KeyboardButton(text="🔹 لغو رزرو")],
            [KeyboardButton(text="🔹 مشاهده وقت‌های رزرو شده")],
            [KeyboardButton(text="🔹 اطلاعات کلینیک")]
        ],
        resize_keyboard=True
    )

def specialty_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="عمومی")],
            [KeyboardButton(text="ارتودنسی")],
            [KeyboardButton(text="ایمپلنت")],
            [KeyboardButton(text="لیزر")],
            [KeyboardButton(text="« بازگشت"), KeyboardButton(text="🏠 منوی اصلی")]
        ],
        resize_keyboard=True
    )

def date_menu():
    dates = get_next_7_days()
    buttons = []
    row = []
    for d in dates:
        jalali = gregorian_to_jalali(d.strftime("%Y-%m-%d"))
        row.append(KeyboardButton(text=jalali))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([KeyboardButton(text="« بازگشت"), KeyboardButton(text="🏠 منوی اصلی")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def time_inline_keyboard(available_times, date_greg):
    buttons = []
    for t in available_times:
        buttons.append([InlineKeyboardButton(
            text=t,
            callback_data=f"select_time:{date_greg}:{t}"
        )])
    buttons.append([InlineKeyboardButton(text="« بازگشت", callback_data="back_to_date")])
    # دکمه منوی اصلی در inline هم اضافه شد
    buttons.append([InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)