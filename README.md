# 📝 Wiki Translator

**ابزار هوشمند ترجمه و پردازش مقالات ویکی‌پدیا با استفاده از مدل‌های زبانی Gemini**

فارسی · English

---

🇮🇷 **فارسی**

## 📖 معرفی

**Wiki Translator** (نسخه ۵.۱) یک ابزار پایتونی پیشرفته برای دریافت، پردازش و ترجمهٔ مقالات ویکی‌پدیا از انگلیسی به فارسی است.

این پروژه با هدف ساده‌تر کردن فرایند ترجمه و آماده‌سازی محتوای مقالات برای استفاده در ویکی‌پدیای فارسی توسعه داده شده و از **Google Gemini** برای ترجمه و بازبینی هوشمند استفاده می‌کند.

ویژگی‌های کلیدی نسخه ۵.۱:
- ترجمهٔ **بخش‌محور** (Section-aware chunking)
- بازسازی هوشمند لینک‌های داخلی و تطبیق رده‌ها (Categories)
- حذف لینک‌های قرمز تأییدشده
- بازبینی نهایی با هوش مصنوعی
- رابط گرافیکی مدرن با تم تاریک پیش‌فرض، کارت‌های آماری و درخت وضعیت مقالات
- مدیریت هوشمند چند API Key با اولویت‌بندی خطا و محدودیت نرخ

## ✨ امکانات

| قابلیت | توضیح |
|--------|--------|
| 🌐 دریافت محتوا | دریافت ویکی‌کد مقالات و اعضای رده از Wikipedia API |
| 🤖 ترجمه هوشمند | ترجمه با Gemini (مدل پیش‌فرض: `gemini-3.5-flash-lite`) |
| 📑 تقسیم بخش‌محور | ترجیح تقسیم بر اساس تیترهای `==` و در صورت نیاز پاراگراف |
| 🔗 مدیریت لینک | استخراج لینک‌ها، نگاشت به نسخه فارسی (langlinks)، بازسازی لینک‌های متنی و تبدیل `[[en]]` → `[[fa]]` |
| 🏷️ تطبیق رده‌ها | استخراج `Category:`، نگاشت به `[[رده:...]]` و حذف رده‌های بدون معادل |
| 🧹 پاکسازی | حذف لینک‌های قرمز تأییدشده + محافظت از قالب‌ها و ارجاعات |
| 🔍 بازبینی AI | بازبینی تکه‌تکه با همپوشانی برای انسجام و کیفیت نهایی |
| 🖥️ رابط گرافیکی | تم تاریک/روشن، کارت‌های آماری، نوار پیشرفت، درخت وضعیت مقالات، Pause/Resume/Stop |
| 🔑 مدیریت کلید | پشتیبانی از چند API Key، امتیازدهی بر اساس خطای ۴۲۹، باطل‌سازی کلید نامعتبر |
| 🔄 تلاش مجدد | مدیریت هوشمند خطاهای شبکه و محدودیت نرخ |
| 📝 لاگ کامل | ثبت رویدادها و خطاها در سیستم لاگ |
| 🧩 معماری ماژولار | ساختار تمیز و قابل توسعه |

## 🏗️ معماری پروژه

```
wiki-translator/
│
├── main.py                  # نقطهٔ ورود اصلی
├── config.py                # تنظیمات، مسیرها و پرامپت‌ها
├── key_manager.py           # مدیریت و توزیع API Keyها
├── logger_setup.py          # تنظیم سیستم لاگ
├── translator_core.py       # هستهٔ ترجمه، بازبینی و pipeline
├── wikipedia_api.py         # ارتباط با Wikipedia API + پردازش ویکی‌کد
├── utils.py                 # توابع کمکی (تقسیم متن، مرتب‌سازی فارسی و ...)
├── wiki_translator_gui.py   # نقطهٔ ورود رابط گرافیکی
├── requirements.txt
├── .gitignore
│
├── ui/
│   ├── app.py               # منطق رابط کاربری
│   ├── styles.py            # تم و استایل‌ها
│   └── __init__.py
│
├── input/                   # ویکی‌کد خام مقالات (تولید خودکار)
├── translated/              # خروجی مقالات ترجمه‌شده
├── .progress/               # ذخیرهٔ پیشرفت برای ادامهٔ ترجمه
└── logs/                    # فایل‌های لاگ
```

### اجزای اصلی

| فایل | توضیح |
|------|--------|
| `main.py` | نقطهٔ ورود اصلی برنامه |
| `translator_core.py` | هستهٔ ترجمه، فراخوانی Gemini، ترجمه عنوان، بازبینی و pipeline کامل |
| `wikipedia_api.py` | ارتباط با Wikipedia API، استخراج لینک/رده، تطبیق langlinks، حذف لینک قرمز و پاکسازی |
| `key_manager.py` | مدیریت چند کلید، امتیازدهی، تشخیص ۴۲۹ و باطل‌سازی کلید نامعتبر |
| `config.py` | تنظیمات، مسیرها، محدودیت‌ها و پرامپت‌های سیستم |
| `utils.py` | تقسیم متن بخش‌محور، مرتب‌سازی فارسی، توابع کمکی |
| `logger_setup.py` | پیکربندی سیستم ثبت لاگ |
| `ui/app.py` | رابط گرافیکی کامل (کنترل، آمار، درخت مقالات، لاگ رنگی) |
| `ui/styles.py` | تم تاریک/روشن و استایل‌ها |

## 🧠 فرایند ترجمه (Pipeline)

```
Wikipedia
    │
    ▼
دریافت ویکی‌کد مقاله
    │
    ▼
استخراج لینک‌های داخلی + نگاشت به نسخه فارسی (langlinks)
    │
    ▼
استخراج رده‌ها + نگاشت به رده‌های فارسی
    │
    ▼
ترجمهٔ عنوان مقاله
    │
    ▼
تقسیم بخش‌محور (Section-aware chunking)
    │
    ▼
ترجمهٔ هر تکه با لیست لینک‌های مربوطه (Gemini)
    │
    ▼
بازسازی لینک‌های متن ساده از روی fa_map
    │
    ▼
تبدیل [[عنوان انگلیسی]] → [[عنوان فارسی]]
    │
    ▼
تطبیق رده‌ها (Category → رده)
    │
    ▼
حذف لینک‌های قرمز تأییدشده
    │
    ▼
بازبینی نهایی با AI (تکه‌تکه + همپوشانی)
    │
    ▼
پاکسازی نهایی و ذخیرهٔ مقاله
```

## ⚙️ پیش‌نیازها

- Python **3.10** یا بالاتر (پیشنهاد: **3.12**)
- اتصال اینترنت
- یک یا چند **Google Gemini API Key**
- دسترسی به Wikipedia API

## 🚀 نصب

```bash
git clone https://github.com/Arian021h/wiki-translator.git
cd wiki-translator
```

ایجاد محیط مجازی:

**Windows**
```powershell
python -m venv .venv
.venv\Scripts\activate
```

**Linux / macOS**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

نصب وابستگی‌ها:
```bash
pip install -r requirements.txt
```

## 🔑 تنظیم API Key

کلیدها **هرگز** داخل کد ذخیره نمی‌شوند و از متغیر محیطی خوانده می‌شوند.

### یک کلید
**Windows PowerShell:**
```powershell
$env:GEMINI_API_KEY="YOUR_API_KEY"
```

**Linux / macOS:**
```bash
export GEMINI_API_KEY="YOUR_API_KEY"
```

### چند کلید
```powershell
$env:GEMINI_API_KEYS="KEY_1,KEY_2,KEY_3"
```
یا
```bash
export GEMINI_API_KEYS="KEY_1,KEY_2,KEY_3"
```

> ⚠️ هرگز کلید واقعی را داخل GitHub، کد منبع یا فایل‌های عمومی قرار ندهید.

## ▶️ اجرای برنامه

پس از فعال کردن محیط مجازی و تنظیم کلید:

```bash
python main.py
```

یا مستقیماً رابط گرافیکی:

```bash
python wiki_translator_gui.py
```

## 🖥️ رابط گرافیکی

- تم تاریک پیش‌فرض + امکان تغییر به روشن
- کارت‌های آماری زنده (موفق، ناموفق، در حال انجام و ...)
- نوار پیشرفت کلی
- درخت وضعیت مقالات با برچسب‌های رنگی
- داشبورد وضعیت کلیدهای API
- لاگ رنگی با سطوح مختلف
- دکمه‌های Pause / Resume / Stop
- پشتیبانی از ترجمه بر اساس رده یا لیست مقالات

## 🔐 امنیت

- کلیدها فقط از طریق Environment Variable خوانده می‌شوند.
- موارد زیر در `.gitignore` قرار دارند و نباید در Repository باشند:

```
.env
*.env
logs/
__pycache__/
.progress/
input/
translated/
```

## 📋 مدیریت چند کلید API

کلاس `KeyManager` مسئولیت‌های زیر را بر عهده دارد:

- توزیع درخواست‌ها بین کلیدهای موجود
- امتیازدهی بر اساس تعداد خطای ۴۲۹ و موفقیت
- باطل‌سازی خودکار کلیدهای نامعتبر
- نمایش وضعیت لحظه‌ای کلیدها در رابط کاربری

این قابلیت برای حجم بالای ترجمه بسیار مفید است.

## 🛠️ وضعیت پروژه

🚧 **در حال توسعه فعال** (نسخه ۵.۱)

برخی بخش‌ها ممکن است در نسخه‌های آینده تغییر یا بهبود یابند.

## 🔮 برنامهٔ توسعه

- پشتیبانی بهتر از ساختارهای پیچیدهٔ WikiText (جدول، قالب‌های تو در تو و ...)
- بهبود کیفیت و یکدستی ترجمه
- سیستم صف ترجمه پیشرفته‌تر
- امکان انتخاب مدل زبانی از رابط کاربری
- پشتیبانی از زبان‌های مبدأ/مقصد بیشتر
- گزارش‌های آماری کامل‌تر از عملیات ترجمه
- بهبود پردازش Templateها و Referenceها

## 🤝 مشارکت

Pull Requestها و پیشنهادهای بهبود مورد استقبال هستند.

```bash
git checkout -b feature/my-feature
# تغییرات را اعمال کنید
git add .
git commit -m "Add new feature"
git push origin feature/my-feature
```

سپس یک Pull Request باز کنید.

## ⚠️ نکات مهم

این نرم‌افزار صرفاً یک **ابزار کمکی** برای ترجمه و پردازش محتوا است.

خروجی ترجمه **باید** قبل از انتشار در ویکی‌پدیا توسط کاربر بررسی و ویرایش شود.

استفاده از APIهای شخص ثالث تابع قوانین، محدودیت‌ها و شرایط استفادهٔ ارائه‌دهندگان آن‌ها است.

## 📄 مجوز

مجوز پروژه در نسخه‌های بعدی مشخص خواهد شد.

---

🇬🇧 **English**

## 📖 Overview

**Wiki Translator** (v5.1) is a Python tool for retrieving, processing, and translating Wikipedia articles from English to Persian.

It uses **Google Gemini** for high-quality AI translation and review, while carefully preserving WikiText structure, internal links, categories, and references.

Key highlights of v5.1:
- **Section-aware** chunking
- Intelligent internal link reconstruction & category adaptation
- Confirmed red-link removal
- AI-powered final review
- Modern dark-first GUI with metric cards, status tree, and pause/resume
- Smart multi-API-key management with rate-limit prioritization

## ✨ Features

- 🌐 Fetch article content and category members from Wikipedia API
- 🤖 AI translation powered by Gemini (`gemini-3.5-flash-lite`)
- 📑 Section-aware text splitting (prefer `==` sections, fallback to paragraphs)
- 🔗 Link extraction → langlinks mapping → plain-text link rebuild → `[[en]]` → `[[fa]]`
- 🏷️ Category extraction and adaptation to Persian `[[رده:...]]`
- 🧹 Removal of confirmed red links + protection of templates/references
- 🔍 Chunked AI review with overlap for consistency
- 🖥️ Modern GUI (dark theme by default, metric cards, colored status tree, pause/resume/stop)
- 🔑 Multi-key support with scoring, 429 handling, and invalid-key invalidation
- 🔄 Robust retry logic for network and rate-limit errors
- 📝 Comprehensive logging
- 🧩 Modular and extensible architecture

## 🏗️ Project Structure

```
wiki-translator/
├── main.py
├── config.py
├── key_manager.py
├── logger_setup.py
├── translator_core.py
├── wikipedia_api.py
├── utils.py
├── wiki_translator_gui.py
├── requirements.txt
├── ui/
│   ├── app.py
│   ├── styles.py
│   └── __init__.py
├── input/
├── translated/
├── .progress/
└── logs/
```

## 🧠 Translation Pipeline

```
Wikipedia
    │
    ▼
Fetch wikitext
    │
    ▼
Extract internal links + map to FA via langlinks
    │
    ▼
Extract categories + map to Persian categories
    │
    ▼
Translate title
    │
    ▼
Section-aware chunking
    │
    ▼
Translate each chunk (with relevant link list)
    │
    ▼
Rebuild plain-text links from fa_map
    │
    ▼
Convert [[en]] → [[fa]]
    │
    ▼
Adapt categories (Category → رده)
    │
    ▼
Remove confirmed red links
    │
    ▼
AI review (chunked + overlap)
    │
    ▼
Final cleanup & save
```

## ⚙️ Requirements

- Python 3.10+ (3.12 recommended)
- Internet connection
- One or more Google Gemini API keys
- Wikipedia API access

## 🚀 Installation

```bash
git clone https://github.com/Arian021h/wiki-translator.git
cd wiki-translator
python -m venv .venv
# activate the virtual environment
pip install -r requirements.txt
```

## 🔑 API Key Configuration

Keys are loaded from environment variables only.

**Single key:**
```bash
export GEMINI_API_KEY="YOUR_API_KEY"
```

**Multiple keys:**
```bash
export GEMINI_API_KEYS="KEY_1,KEY_2,KEY_3"
```

Never commit real API keys to the repository.

## ▶️ Running

```bash
python main.py
# or
python wiki_translator_gui.py
```

## 🛠️ Project Status

🚧 **Actively developed** (v5.1)

## ⚠️ Disclaimer

This tool is intended as an **assistance** utility.  
All generated translations **must** be reviewed and edited by a human before being published on Wikipedia.

Use of third-party APIs is subject to their respective terms and quotas.

## 📄 License

License will be specified in a future release.
