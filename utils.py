import random
import string
from datetime import datetime, timedelta
import jdatetime

def generate_reservation_code():
    today = datetime.now().strftime("%Y%m%d")
    rand = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"LS-{today}-{rand}"

def get_next_7_days():
    today = datetime.now().date()
    return [(today + timedelta(days=i)) for i in range(7)]

def jalali_to_gregorian(j_date_str: str) -> str:
    # فرمت ورودی: 1403/02/05
    jy, jm, jd = map(int, j_date_str.split('/'))
    g_date = jdatetime.date(jy, jm, jd).togregorian()
    return g_date.strftime("%Y-%m-%d")

def gregorian_to_jalali(g_date_str: str) -> str:
    g = datetime.strptime(g_date_str, "%Y-%m-%d").date()
    j = jdatetime.date.fromgregorian(date=g)
    return j.strftime("%Y/%m/%d")