import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile

# ================= CONFIG =================
TOKEN = "8360784420:AAEZ0sR4V_erE0FjRmTI4RLeK51sxBddbo8"
ADMINS = [8503115617, 6761125512, 6617032248]

UPI_ID = "rahu1whereim@ptyes"
BINANCE_ID = "1189640561"

INR = 93
DB = "bot.db"

bot = Bot(TOKEN)
dp = Dispatcher()

# ================= DATABASE =================
async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 0
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product TEXT,
            plan TEXT,
            price INTEGER,
            status TEXT
        )
        """)
        await db.commit()

async def add_user(uid):
    async with aiosqlite.connect(DB) as db:
        await db.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (uid,))
        await db.commit()

async def get_balance(uid):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT balance FROM users WHERE id=?", (uid,))
        row = await cur.fetchone()
        return row[0] if row else 0

async def update_balance(uid, amt):
    async with aiosqlite.connect(DB) as db:
        await db.execute("UPDATE users SET balance = balance + ? WHERE id=?", (amt, uid))
        await db.commit()

async def add_order(uid, product, plan, price):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT INTO orders (user_id, product, plan, price, status) VALUES (?, ?, ?, ?, ?)",
            (uid, product, plan, price, "pending")
        )
        await db.commit()

# ================= PRODUCTS =================
PRODUCTS = {
    "ios": {
        "fluorite": [("1 Day",5),("7 Day",15),("30 Day",25)],
        "migul": [("1 Day",5),("30 Day",20)],
        "proxy": [("1 Day",5),("30 Day",20)],
        "imazing": [("60 Day",15)],
        "dns": [("30 Day",10)]
    },
    "android": {
        "hg": [("1 Day",3),("10 Day",8),("30 Day",18)],
        "dripclient": [("1 Day",3),("10 Day",8),("30 Day",12)],
        "hexxcker": [("1 Day",3),("10 Day",8),("30 Day",12)]
    },
    "pc": {
        "streamer": [("30 Day",20),("Lifetime",30)],
        "streamer_plus": [("30 Day",25),("Lifetime",40)],
        "obsidian": [("30 Day",15),("Lifetime",30)],
        "silent": [("30 Day",15),("Lifetime",23)]
    }
}

# ================= STATE =================
user_data = {}

# ================= MENU =================
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍 Shop", callback_data="shop")],
        [InlineKeyboardButton(text="💰 Balance", callback_data="balance")],
        [InlineKeyboardButton(text="📞 Support", callback_data="support")]
    ])

def back_support_kb(back_cb="shop"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅ Back", callback_data=back_cb)],
        [InlineKeyboardButton(text="📞 Support", callback_data="support")]
    ])

# ================= START =================
@dp.message(Command("start"))
async def start(msg: types.Message):
    await add_user(msg.from_user.id)
    await msg.answer("🔥 Welcome to Marscot Premium Store", reply_markup=main_menu())

# ================= SUPPORT =================
@dp.callback_query(F.data == "support")
async def support(c: types.CallbackQuery):
    text = """📞 SUPPORT

Need help? Contact our admins:

👤 @mar1xff
👤 @bhavisss
👤 @pssysmglr

We usually reply fast ⚡
"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅ Back", callback_data="back")]
    ])
    await c.message.edit_text(text, reply_markup=kb)

# ================= BALANCE =================
@dp.callback_query(F.data == "balance")
async def balance(c: types.CallbackQuery):
    bal = await get_balance(c.from_user.id)
    await c.message.edit_text(f"💰 Your Balance: ₹{bal}", reply_markup=main_menu())

# ================= SHOP =================
@dp.callback_query(F.data == "shop")
async def shop(c: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍎 iOS", callback_data="ios")],
        [InlineKeyboardButton(text="🤖 Android", callback_data="android")],
        [InlineKeyboardButton(text="💻 PC", callback_data="pc")],
        [InlineKeyboardButton(text="⬅ Back", callback_data="back")]
    ])
    await c.message.edit_text("🛒 Select Category:", reply_markup=kb)

@dp.callback_query(F.data == "back")
async def back(c: types.CallbackQuery):
    await c.message.edit_text("🏠 Main Menu", reply_markup=main_menu())

# ================= CATEGORY =================
@dp.callback_query(F.data.in_(["ios","android","pc"]))
async def category(c: types.CallbackQuery):
    cat = PRODUCTS[c.data]
    kb = [[InlineKeyboardButton(text=p.upper(), callback_data=f"prod_{c.data}_{p}")] for p in cat]
    kb.append([InlineKeyboardButton(text="⬅ Back", callback_data="shop")])
    await c.message.edit_text("📦 Select Product:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# ================= PRODUCT =================
@dp.callback_query(F.data.startswith("prod_"))
async def product(c: types.CallbackQuery):
    _, cat, name = c.data.split("_")
    plans = PRODUCTS[cat][name]

    user_data[c.from_user.id] = {"product": name}

    kb = [[InlineKeyboardButton(
        text=f"{plan} - ${price} / ₹{price*INR}",
        callback_data=f"plan_{name}_{plan}_{price}"
    )] for plan, price in plans]

    kb.append([InlineKeyboardButton(text="⬅ Back", callback_data=cat)])
    await c.message.edit_text(f"💰 {name.upper()} Plans:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# ================= PLAN =================
@dp.callback_query(F.data.startswith("plan_"))
async def plan(c: types.CallbackQuery):
    _, name, plan_name, price = c.data.split("_")
    price = int(price)

    user_data[c.from_user.id].update({"plan": plan_name, "price": price})

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 UPI", callback_data="upi")],
        [InlineKeyboardButton(text="🪙 Binance", callback_data="binance")],
        [InlineKeyboardButton(text="⬅ Back", callback_data="shop")],
        [InlineKeyboardButton(text="📞 Support", callback_data="support")]
    ])

    await c.message.edit_text(
        f"🧾 {name.upper()} | {plan_name}\n💰 ${price} / ₹{price*INR}",
        reply_markup=kb
    )

# ================= PAYMENT =================
@dp.callback_query(F.data == "upi")
async def upi(c: types.CallbackQuery):
    data = user_data.get(c.from_user.id)
    if not data:
        await c.message.answer("❌ No active order")
        return

    photo = FSInputFile("qr.jpg")
    await c.message.answer_photo(
        photo,
        caption=f"""💳 UPI PAYMENT

💰 Amount: ₹{data['price'] * INR}
🏦 UPI ID: {UPI_ID}

📸 Send screenshot after payment""",
        reply_markup=back_support_kb("shop")
    )

@dp.callback_query(F.data == "binance")
async def binance(c: types.CallbackQuery):
    data = user_data.get(c.from_user.id)
    if not data:
        await c.message.answer("❌ No active order")
        return

    photo = FSInputFile("binance.jpg")
    await c.message.answer_photo(
        photo,
        caption=f"""🪙 BINANCE PAYMENT

💰 Amount: ${data['price']}
🆔 Binance ID: {BINANCE_ID}

📸 Send screenshot after payment""",
        reply_markup=back_support_kb("shop")
    )

# ================= PAYMENT PROOF =================
@dp.message(F.photo)
async def proof(msg: types.Message):
    uid = msg.from_user.id
    data = user_data.get(uid)
    if not data:
        return

    await add_order(uid, data["product"], data["plan"], data["price"])

    for admin in ADMINS:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Approve", callback_data=f"approve_{uid}"),
                InlineKeyboardButton(text="❌ Deny", callback_data=f"deny_{uid}")
            ]
        ])
        await bot.send_photo(
            admin,
            msg.photo[-1].file_id,
            caption=f"User: {uid}\nProduct: {data['product']}\nPlan: {data['plan']}\nPrice: ${data['price']}",
            reply_markup=kb
        )

    await msg.answer("⏳ Waiting for admin approval")

# ================= ADMIN =================
@dp.callback_query(F.data.startswith("approve_"))
async def approve(c: types.CallbackQuery):
    if c.from_user.id not in ADMINS:
        return
    uid = int(c.data.split("_")[1])
    await bot.send_message(uid, "⚠️ Key system under maintenance\nPlease DM admin @mar1xff @bhavisss @pssysmglr.")

@dp.callback_query(F.data.startswith("deny_"))
async def deny(c: types.CallbackQuery):
    if c.from_user.id not in ADMINS:
        return
    uid = int(c.data.split("_")[1])
    await bot.send_message(uid, "❌ Payment rejected")

# ================= BALANCE ADMIN =================
@dp.message(Command("addbal"))
async def addbal(msg: types.Message):
    if msg.from_user.id not in ADMINS:
        return
    try:
        _, uid, amt = msg.text.split()
        await update_balance(int(uid), int(amt))
        await msg.answer("✅ Balance added")
    except:
        await msg.answer("Usage: /addbal user_id amount")

@dp.message(Command("rembal"))
async def rembal(msg: types.Message):
    if msg.from_user.id not in ADMINS:
        return
    try:
        _, uid, amt = msg.text.split()
        await update_balance(int(uid), -int(amt))
        await msg.answer("✅ Balance removed")
    except:
        await msg.answer("Usage: /rembal user_id amount")

# ================= RUN =================
async def main():
    await init_db()
    print("🚀 BOT RUNNING (FINAL)")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())