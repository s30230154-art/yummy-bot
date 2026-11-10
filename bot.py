import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from google import genai
from google.genai import types

# ============================================================
# CONFIGURATION - ទាញពី Environment Variables (Render Dashboard)
# ============================================================
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
GEMINI_API_KEY     = os.environ["GEMINI_API_KEY"]

# WEBHOOK_URL - ចំណាំ: កំណត់នៅពេល Render ផ្តល់ URL ហើយ
# Format: https://your-service-name.onrender.com
# ប្រសិនបើ WEBHOOK_URL មិនទាន់ set ទេ bot នឹងប្រើ polling mode ជំនួស
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")

# Port ដែល Render ប្រើ (ស្វ័យប្រវត្ត)
PORT = int(os.environ.get("PORT", 8080))

# ============================================================
# GEMINI AI CLIENT
# ============================================================
client = genai.Client(api_key=GEMINI_API_KEY)

# ============================================================
# SYSTEM PROMPT - ព័ត៌មានហាង Yummy តាប៉ែ
# ============================================================
STORE_INSTRUCTIONS = """
អ្នកគឺជាជំនួយការលក់ដូរឌីជីថលរបស់ហាង "Yummy តាប៉ែ"។ តួនាទីរបស់អ្នកគឺជួយអតិថិជនឆ្លើយសំណួរ ណែនាំផលិតផល និងទទួលការកុម្ម៉ង់។

## ព័ត៌មានហាង
- ឈ្មោះហាង៖ Yummy តាប៉ែ
- ម៉ោងបើក៖ ២៤ម៉ោង (បើកគ្រប់ពេលវេលា)
- តម្លៃ៖ ៦,០០០ រៀល
- ថ្លៃដឹកជញ្ជូន៖ ២ ដុល្លារ

## ភាសា និងសម្លេង
- ឆ្លើយជាភាសាខ្មែរជាចម្បង។ បើអតិថិជនសរសេរជាភាសាអង់គ្លេស ត្រូវឆ្លើយជាភាសាអង់គ្លេស។
- ប្រើសម្លេងរួសរាយ រាក់ទាក់ និងសុភាពរាបសា ដូចអ្នកលក់ដែលស្រលាញ់អតិថិជន។
- ចាប់ផ្តើមដោយការស្វាគមន៍ ឧទាហរណ៍៖ "សួស្តី! ស្វាគមន៍មកកាន់ Yummy តាប៉ែ 😊 តើបងចង់កុម្ម៉ង់ ឬចង់ដឹងអ្វីដែរ?" ប្រើតែការស្វាគមន៍ដំបូងប៉ុណ្ណោះ
- ឆ្លើយខ្លី ងាយយល់ មិនវែងឆ្ងាយ។ អាចប្រើ emoji ដោយសមស្រប។

## របៀបតបអតិថិជន
1. សួរអំពីតម្លៃ៖ ប្រាប់ថា តម្លៃ ៦,០០០ រៀល ហើយសួរថាចង់កុម្ម៉ង់ប៉ុន្មាន។
2. សួរអំពីម៉ោងបើក៖ ប្រាប់ថាហាងបើក ២៤ម៉ោង អាចកុម្ម៉ង់បានគ្រប់ពេល។
3. សួរអំពីការដឹកជញ្ជូន៖ ប្រាប់ថាថ្លៃដឹកជញ្ជូន ២ ដុល្លារ។
4. ពេលអតិថិជនចង់កុម្ម៉ង់ ត្រូវប្រមូលព័ត៌មាន៖
   - ចំនួនដែលចង់បាន
   - ឈ្មោះ
   - លេខទូរស័ព្ទ
   - អាសយដ្ឋានដឹកជញ្ជូន
   បន្ទាប់មកសង្ខេបការកុម្ម៉ង់ និងតម្លៃសរុប (តម្លៃទំនិញ + ថ្លៃដឹក) ឱ្យអតិថិជនបញ្ជាក់។
5. បញ្ចប់ដោយអរគុណ ឧទាហរណ៍៖ "អរគុណច្រើនបង! ទំនិញនឹងដឹកជូនឆាប់ៗនេះ ❤️"

## ច្បាប់សំខាន់
- ប្រើតែព័ត៌មានខាងលើប៉ុណ្ណោះ។ បើមិនដឹង (ឧ. ទំហំ រសជាតិ ពេលវេលាដឹកជញ្ជូនជាក់លាក់ ការបញ្ចុះតម្លៃ) កុំប្រឌិតចម្លើយ ត្រូវប្រាប់ថា "សូមរង់ចាំបន្តិច ខ្ញុំនឹងសួរម្ចាស់ហាងឱ្យបង" ឬណែនាំឱ្យទាក់ទងម្ចាស់ហាងផ្ទាល់។
- កុំសន្យាអ្វីដែលមិនមានក្នុងព័ត៌មានហាង។
- បើអតិថិជនមិនពេញចិត្ត ឬមានបណ្តឹង ត្រូវសុំទោសដោយស្មោះ ស្តាប់ឱ្យបានល្អ ហើយបញ្ជូនបន្តទៅម្ចាស់ហាង។
- កុំឆ្លើយសំណួរដែលមិនទាក់ទងនឹងហាង។ ត្រូវនាំការសន្ទនាត្រឡប់មករកការលក់វិញដោយសុភាព។
- មិនត្រូវសុំព័ត៌មានផ្ទាល់ខ្លួនលើសពីអ្វីដែលចាំបាច់សម្រាប់ការកុម្ម៉ង់ទេ។
"""

# ============================================================
# HANDLERS
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ស្វាគមន៍អតិថិជននៅពេលចុច /start"""
    welcome_text = "សួស្តី! ស្វាគមន៍មកកាន់ Yummy តាប៉ែ 😊 តើបងចង់កុម្ម៉ង់ ឬចង់ដឹងអ្វីដែរ?"
    await update.message.reply_text(welcome_text)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ទទួលសារពីអតិថិជន ឱ្យ Gemini AI ឆ្លើយ"""
    customer_message = update.message.text
    user_name = update.effective_user.first_name

    print(f"[{user_name}]: {customer_message}")

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        response = await client.aio.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=customer_message,
            config=types.GenerateContentConfig(
                system_instruction=STORE_INSTRUCTIONS,
            ),
        )
        ai_reply = response.text if response.text else "សូមអភ័យទោស ខ្ញុំមិនអាចឆ្លើយបានទេ។"
        await update.message.reply_text(ai_reply)
        print(f"[Bot -> {user_name}]: {ai_reply[:80]}...")

    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("សូមអភ័យទោសបង ប្រព័ន្ធកំពុងរវល់ សូមព្យាយាមម្តងទៀតនៅបន្តិចទៀតនេះ។")


# ============================================================
# MAIN - ប្រើ Webhook ឬ Polling ស្វ័យប្រវត្ត
# ============================================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    if WEBHOOK_URL:
        # Webhook Mode - ប្រើពេល WEBHOOK_URL បានកំណត់
        print(f"🤖 Yummy Bot ដំណើរការ via Webhook លើ port {PORT}...")
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=f"{WEBHOOK_URL}/webhook",
        )
    else:
        # Polling Mode - ប្រើពេលដំបូងមុន WEBHOOK_URL ត្រូវបានកំណត់
        print("🤖 Yummy Bot ដំណើរការ via Polling (WEBHOOK_URL មិនទាន់កំណត់)...")
        app.run_polling()
