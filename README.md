# wiki-translator
Smart Wikipedia article translator (EN→FA) powered by Gemini. Section-aware, link/category adaptation, AI review &amp; modern dark UI

# 📝 Wiki Translator

**ابزار هوشمند ترجمه و پردازش مقالات ویکی‌پدیا با استفاده از مدل‌های زبانی Gemini**

[فارسی](#-فارسی) · [English](#-english)

---

# 🇮🇷 فارسی

## 📖 معرفی

**Wiki Translator** یک ابزار پایتونی برای دریافت، پردازش و ترجمهٔ مقالات ویکی‌پدیا است که با هدف ساده‌تر کردن فرایند ترجمه و آماده‌سازی محتوای مقالات برای استفاده در ویکی‌پدیا توسعه داده شده است.

این پروژه از **Google Gemini API** برای ترجمه و پردازش هوشمند متن استفاده می‌کند و در کنار آن، قابلیت دریافت اطلاعات و محتوای مقالات از **Wikipedia API** را دارد.

این برنامه دارای یک رابط گرافیکی برای مدیریت فرایند ترجمه است و می‌تواند با استفاده از چند API Key، درخواست‌های ترجمه را میان کلیدهای مختلف توزیع کند.

---

## ✨ امکانات

* 🌐 دریافت اطلاعات و محتوای مقالات از Wikipedia
* 🤖 ترجمهٔ متن با استفاده از Google Gemini
* 🖥️ رابط گرافیکی برای اجرای آسان برنامه
* 🔑 پشتیبانی از چند API Key
* ⚡ مدیریت و توزیع درخواست‌ها میان کلیدهای API
* 🔄 مدیریت خطا و تلاش مجدد برای درخواست‌های ناموفق
* 🛡️ مدیریت امن کلیدهای API از طریق متغیرهای محیطی
* 🧹 پردازش و آماده‌سازی محتوای ویکی
* 📚 پشتیبانی از ترجمهٔ مقالات و دسته‌بندی‌های ویکی‌پدیا
* 📝 ثبت خطاها و رویدادهای برنامه در سیستم لاگ
* 🧩 معماری ماژولار و قابل توسعه

---

## 🏗️ معماری پروژه

ساختار کلی پروژه به شکل زیر است:

```text
wiki-translator/
│
├── main.py
├── config.py
├── key_manager.py
├── logger_setup.py
├── translator_core.py
├── wikipedia_api.py
├── utils.py
├── wiki_translator_gui.py
├── requirements.txt
├── .gitignore
│
├── ui/
│   ├── app.py
│   ├── styles.py
│   └── __init__.py
│
└── logs/
```

### اجزای اصلی

| فایل                     | توضیح                                        |
| ------------------------ | -------------------------------------------- |
| `main.py`                | نقطهٔ ورود اصلی برنامه                       |
| `translator_core.py`     | هستهٔ ترجمه و ارتباط با مدل زبانی            |
| `wikipedia_api.py`       | ارتباط با Wikipedia API و پردازش محتوای ویکی |
| `key_manager.py`         | مدیریت و توزیع API Keyها                     |
| `config.py`              | تنظیمات اصلی برنامه                          |
| `utils.py`               | توابع کمکی                                   |
| `logger_setup.py`        | تنظیم سیستم ثبت لاگ                          |
| `wiki_translator_gui.py` | اجرای رابط گرافیکی                           |
| `ui/app.py`              | منطق رابط کاربری                             |
| `ui/styles.py`           | تنظیمات ظاهری رابط کاربری                    |

---

## ⚙️ پیش‌نیازها

برای اجرای پروژه به موارد زیر نیاز دارید:

* Python 3.10 یا بالاتر
* اتصال اینترنت
* یک یا چند Google Gemini API Key
* دسترسی به Wikipedia API

پیشنهاد می‌شود از **Python 3.12** استفاده کنید.

---

## 🚀 نصب

ابتدا پروژه را دریافت کنید:

```bash
git clone https://github.com/Arian021h/wiki-translator.git
cd wiki-translator
```

سپس یک محیط مجازی ایجاد کنید:

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

وابستگی‌ها را نصب کنید:

```bash
pip install -r requirements.txt
```

---

## 🔑 تنظیم API Key

این پروژه کلیدهای Gemini را مستقیماً داخل کد ذخیره نمی‌کند و آن‌ها را از **Environment Variable** دریافت می‌کند.

### یک API Key

در Windows PowerShell:

```powershell
$env:GEMINI_API_KEY="YOUR_API_KEY"
```

در Linux / macOS:

```bash
export GEMINI_API_KEY="YOUR_API_KEY"
```

### چند API Key

برای استفاده از چند کلید:

```powershell
$env:GEMINI_API_KEYS="KEY_1,KEY_2,KEY_3"
```

یا:

```powershell
$env:GOOGLE_API_KEYS="KEY_1,KEY_2,KEY_3"
```

کلید واقعی خود را هرگز داخل GitHub، کد منبع یا فایل‌های عمومی قرار ندهید.

---

## ▶️ اجرای برنامه

پس از فعال کردن محیط مجازی و تنظیم API Key:

```bash
python main.py
```

در صورت استفاده از رابط گرافیکی:

```bash
python wiki_translator_gui.py
```

---

## 🧠 فرایند کلی ترجمه

فرایند اصلی برنامه به صورت کلی شامل مراحل زیر است:

```text
Wikipedia
    │
    ▼
دریافت مقاله
    │
    ▼
پردازش محتوای Wiki
    │
    ▼
تقسیم و آماده‌سازی متن
    │
    ▼
Google Gemini
    │
    ▼
ترجمه و پردازش
    │
    ▼
بازسازی محتوا
    │
    ▼
مقالهٔ ترجمه‌شده
```

---

## 🔐 امنیت

این پروژه از Environment Variable برای دریافت API Key استفاده می‌کند.

فایل‌های زیر نباید در Repository قرار بگیرند:

```text
.env
*.env
logs/
__pycache__/
```

این موارد در `.gitignore` پروژه قرار گرفته‌اند.

**هیچ API Key یا Token واقعی را در کد منبع قرار ندهید.**

---

## 📋 مدیریت چند کلید API

در صورتی که چند API Key در اختیار برنامه قرار داده شود، `KeyManager` وظیفهٔ مدیریت آن‌ها را بر عهده دارد.

این قابلیت برای پروژه‌هایی که تعداد زیادی درخواست ترجمه ارسال می‌کنند می‌تواند مفید باشد و امکان مدیریت وضعیت کلیدها و استفادهٔ مناسب‌تر از ظرفیت موجود را فراهم می‌کند.

---

## 🛠️ وضعیت پروژه

> 🚧 این پروژه در حال توسعه است.

برخی بخش‌ها ممکن است در نسخه‌های آینده تغییر کنند یا بهبود داده شوند.

---

## 🔮 برنامهٔ توسعه

قابلیت‌های احتمالی آینده:

* [ ] پشتیبانی بهتر از ترجمهٔ ساختارهای پیچیدهٔ WikiText
* [ ] بهبود کیفیت ترجمه
* [ ] مدیریت پیشرفته‌تر خطاهای API
* [ ] سیستم صف ترجمه
* [ ] امکان توقف و ادامهٔ عملیات ترجمه
* [ ] نمایش پیشرفت ترجمه
* [ ] تنظیمات پیشرفته‌تر رابط کاربری
* [ ] پشتیبانی از مدل‌های زبانی بیشتر
* [ ] امکان انتخاب زبان مبدأ و مقصد
* [ ] بهبود پردازش Templateها و Referenceها
* [ ] ایجاد گزارش کامل از عملیات ترجمه

---

## 🤝 مشارکت

Pull Requestها و پیشنهادهای بهبود پروژه مورد استقبال هستند.

برای مشارکت:

```bash
git fork
git clone
git checkout -b feature/my-feature
```

پس از اعمال تغییرات:

```bash
git add .
git commit -m "Add new feature"
git push origin feature/my-feature
```

سپس می‌توانید یک Pull Request ایجاد کنید.

---

## ⚠️ نکات مهم

این نرم‌افزار صرفاً یک ابزار کمکی برای ترجمه و پردازش محتوا است.

خروجی ترجمه باید **قبل از انتشار در ویکی‌پدیا توسط کاربر بررسی و ویرایش شود**.

همچنین استفاده از APIهای شخص ثالث تابع قوانین، محدودیت‌ها و شرایط استفادهٔ ارائه‌دهندگان آن‌ها است.

---

## 📄 مجوز

مجوز پروژه را می‌توان در نسخه‌های بعدی مشخص کرد.

---

# 🇬🇧 English

## 📖 Overview

**Wiki Translator** is a Python-based tool for retrieving, processing, and translating Wikipedia articles.

The project is designed to simplify the workflow of translating and preparing Wikipedia content for further editing and publication.

It uses the **Google Gemini API** for AI-powered translation and text processing and communicates with the **Wikipedia API** to retrieve article content and metadata.

The application also provides a graphical user interface and supports managing multiple API keys for large translation workloads.

---

## ✨ Features

* 🌐 Retrieve Wikipedia articles and metadata
* 🤖 AI-powered translation using Google Gemini
* 🖥️ Graphical user interface
* 🔑 Multiple API key support
* ⚡ API key management and request distribution
* 🔄 Error handling and retry mechanisms
* 🛡️ Environment-based API key configuration
* 📚 Wikipedia category-based workflows
* 🧹 Wiki content processing
* 📝 Application logging
* 🧩 Modular and extensible architecture

---

## 🏗️ Project Structure

```text
wiki-translator/
│
├── main.py
├── config.py
├── key_manager.py
├── logger_setup.py
├── translator_core.py
├── wikipedia_api.py
├── utils.py
├── wiki_translator_gui.py
├── requirements.txt
├── .gitignore
│
├── ui/
│   ├── app.py
│   ├── styles.py
│   └── __init__.py
│
└── logs/
```

### Main Components

| File                     | Description                                         |
| ------------------------ | --------------------------------------------------- |
| `main.py`                | Main application entry point                        |
| `translator_core.py`     | Translation engine and LLM communication            |
| `wikipedia_api.py`       | Wikipedia API communication and WikiText processing |
| `key_manager.py`         | API key management                                  |
| `config.py`              | Application configuration                           |
| `utils.py`               | Utility functions                                   |
| `logger_setup.py`        | Logging configuration                               |
| `wiki_translator_gui.py` | GUI entry point                                     |
| `ui/app.py`              | GUI application logic                               |
| `ui/styles.py`           | GUI styling                                         |

---

## ⚙️ Requirements

You will need:

* Python 3.10+
* Internet connection
* One or more Google Gemini API keys
* Access to the Wikipedia API

**Python 3.12 is recommended.**

---

## 🚀 Installation

Clone the repository:

```bash
git clone https://github.com/Arian021h/wiki-translator.git
cd wiki-translator
```

Create a virtual environment:

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

---

## 🔑 API Key Configuration

API keys should **not** be hard-coded into the source code.

The application reads Gemini credentials from environment variables.

### Single API Key

Windows PowerShell:

```powershell
$env:GEMINI_API_KEY="YOUR_API_KEY"
```

Linux / macOS:

```bash
export GEMINI_API_KEY="YOUR_API_KEY"
```

### Multiple API Keys

```powershell
$env:GEMINI_API_KEYS="KEY_1,KEY_2,KEY_3"
```

or:

```powershell
$env:GOOGLE_API_KEYS="KEY_1,KEY_2,KEY_3"
```

Never commit real API keys, passwords, tokens, or other secrets to GitHub.

---

## ▶️ Running the Application

After activating the virtual environment and configuring the API key:

```bash
python main.py
```

To launch the graphical interface:

```bash
python wiki_translator_gui.py
```

---

## 🧠 Translation Workflow

The general workflow looks like this:

```text
Wikipedia
    │
    ▼
Article Retrieval
    │
    ▼
WikiText Processing
    │
    ▼
Text Preparation
    │
    ▼
Google Gemini
    │
    ▼
Translation & Processing
    │
    ▼
Content Reconstruction
    │
    ▼
Translated Article
```

---

## 🔐 Security

API credentials are loaded through environment variables instead of being stored directly in the source code.

The following files and directories should not be committed:

```text
.env
*.env
logs/
__pycache__/
```

These are already excluded through `.gitignore`.

**Never publish real API keys or tokens in the repository.**

---

## 📋 Multiple API Key Management

When multiple API keys are provided, the `KeyManager` component manages the available keys and their usage.

This can be useful for applications that perform a large number of translation requests and need a centralized way to manage multiple API credentials.

---

## 🛠️ Project Status

> 🚧 **Work in Progress**

The project is actively being developed and some components may change in future versions.

---

## 🔮 Roadmap

Possible future improvements include:

* [ ] Better support for complex WikiText structures
* [ ] Improved translation quality
* [ ] Advanced API error handling
* [ ] Translation queue system
* [ ] Pause and resume translation jobs
* [ ] Translation progress tracking
* [ ] Advanced GUI configuration
* [ ] Support for additional language models
* [ ] Source and target language selection
* [ ] Improved Template and Reference processing
* [ ] Detailed translation reports

---

## 🤝 Contributing

Contributions, suggestions, and pull requests are welcome.

A typical workflow:

```bash
git fork
git clone
git checkout -b feature/my-feature
```

After making your changes:

```bash
git add .
git commit -m "Add new feature"
git push origin feature/my-feature
```

Then open a Pull Request.

---

## ⚠️ Disclaimer

This software is intended as an **assistance tool for translation and content processing**.

Generated translations should be **reviewed and edited by a human before being published on Wikipedia**.

Use of third-party APIs is subject to the terms, policies, quotas, and limitations of their respective providers.

---

## 📄 License

The project license can be defined in a future release.
