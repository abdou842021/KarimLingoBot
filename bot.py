وعimport requests
from io import BytesIO
from gtts import gTTS
from deep_translator import GoogleTranslator
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8908406408:AAF3ocv-g_xSxgVRnJRMSzTncYj7hs2JOus"

# الكلمات المفتاحية اللي غادي يفهمها البوت
KEYWORDS = ["نطق", "شرح", "معنى", "translate", "pronounce", "؟"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحبا!\n\n"
        "فالمجموعة:\n"
        "رد على أي رسالة واكتب مثلاً:\n"
        "نطق beautiful\n"
        "أو\n"
        "شرح beautiful\n\n"
        "غادي نترجمها وننطقها ليك."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text:
        return

    # نتأكدو واش الرسالة فيها كلمة مفتاحية
    lower_text = text.lower()
    triggered = False
    word = None

    for key in KEYWORDS:
        if lower_text.startswith(key + " "):
            word = text[len(key):].strip().lower()
            triggered = True
            break
        elif lower_text == key:
            await update.message.reply_text(
                "كتب الكلمة بعد الكلمة المفتاحية.\nمثال: نطق beautiful"
            )
            return

    # إلا ماكانتش كلمة مفتاحية، نرجعو للمنطق القديم
    if not triggered:
        words = text.split()
        is_single_word = len(words) == 1 and words[0].isalpha()

        if is_single_word:
            word = words[0].lower()
            triggered = True
        else:
            # جملة عادية → نطق فقط
            await update.message.reply_text("كنقرا النص... 🔊")
            tts = gTTS(text=text, lang="en", tld="us")
            audio_fp = BytesIO()
            tts.write_to_fp(audio_fp)
            audio_fp.seek(0)
            await update.message.reply_voice(voice=audio_fp)
            return

    # هنا وصلنا لكلمة بغينا نشرحوها
    if not word or not word.isalpha():
        await update.message.reply_text("الكلمة خاصها تكون إنجليزية فقط.")
        return

    await update.message.reply_text(f"كاينبحث على: {word} ... ⏳")

    try:
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            await update.message.reply_text("ما لقيتش هاد الكلمة.")
            return

        data = response.json()[0]

        # الفونتيك
        phonetic = data.get("phonetic", "")
        if not phonetic and data.get("phonetics"):
            for p in data["phonetics"]:
                if p.get("text"):
                    phonetic = p["text"]
                    break

        # التعريف
        definition_en = ""
        if data.get("meanings"):
            defs = data["meanings"][0].get("definitions", [])
            if defs:
                definition_en = defs[0].get("definition", "")

        if not definition_en:
            await update.message.reply_text("ما لقيتش تعريف واضح.")
            return

        definition_ar = GoogleTranslator(
            source="en",
            target="ar"
        ).translate(definition_en)

        reply = f"""
📖 *الكلمة:* `{word}`

🔊 *الفونتيك:* `{phonetic}`

🇩🇿 *المعنى:*
{definition_ar}
"""

        await update.message.reply_text(
            reply,
            parse_mode="Markdown"
        )

        # النطق
        tts = gTTS(text=word, lang="en", tld="us")
        audio_fp = BytesIO()
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)

        await update.message.reply_voice(
            voice=audio_fp,
            caption=f"النطق: {word}"
        )

    except Exception as e:
        await update.message.reply_text(
            f"وقع خطأ: {str(e)}"
        )


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    print("البوت خدام...")
    app.run_polling()


if __name__ == "__main__":
    main()
