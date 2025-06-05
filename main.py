#
# -*- coding: utf-8 -*-

import logging
import os
import asyncio
import threading

try:
    import aiohttp.web
except ImportError:
    aiohttp = None
from http.server import BaseHTTPRequestHandler, HTTPServer

# ---------------------- ВСТАВКА: Простой HTTP-сервер ----------------------
#
# Этот код запускает маленький HTTP-сервер на порту из переменной окружения PORT.
# Render автоматически задаёт PORT, и благодаря этому сервер «увидит» открытый порт,
# не завершит Web Service с ошибкой «no open ports detected».
#
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Всегда отвечаем 200 OK
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"OK")

def start_http_server():
    port = int(os.environ.get("PORT", "8080"))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

# Запускаем HTTP-сервер в отдельном потоке, чтобы не блокировать бота
threading.Thread(target=start_http_server, daemon=True).start()
# ------------------------------------------------------------------------------

import sys, logging
from pathlib import Path

import asyncio
try:
    import aiohttp.web
except ImportError:
    aiohttp = None

from dotenv import load_dotenv
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram.error import BadRequest

# Logging
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s: %(message)s",
)

# Load environment
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "https://t.me/digitaI_age")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@digitaI_age")

# Рекомендації для росту (чек-лист)
RECOMMENDATIONS = {
    "Начинающий (ниже Junior)": [
        "Ти щойно почав свій шлях у світі дизайну. Навчився базових інструментів – знаєш основи роботи в Figma чи Sketch, вмієш створювати прості макети за готовими гайдлайнами, але ще не знаєш, як аргументувати власні рішення. Твої дизайни часто потребують доопрацювання від старших колег: ти іноді не дотримуєшся принципів вирівнювання або робиш елементи «на око». Портфоліо складається з академічних чи студентських робіт: кілька статичних екранів без глибоких досліджень або адаптивних версій. Знімаєш час на пошук вакансій: відгукуєшся на всі джуниор-позиції й часто отримуєш відмови, адже вимагається хоч невеликий практичний досвід. "
        "У твому розпорядженні чек-ліст: відпрацювати навички прототипування, навчитися робити прості клікабельні макети, освоїти гайдлайни компаній (Apple, Google), підготувати перше згідне з UX-базою резюме та оновити портфоліо на Behance/Dribbble. Поки що ти шукаєш менторів, відвідуюш вебінари з дизайну та виконуєш завдання з безкоштовних онлайн-курсів. Твоє головне завдання – довести, що вмієш доводити власні рішення: навчитися складати короткі кейси, описувати, чому вибрав певну сітку, колір і шрифт",
    ],
    "Junior": [
        "Ти вже маєш перший досвід у реальних проектах – можливо, стажування в студії або фриланс із дрібними замовленнями. Впевнено оперуєш Figma: створюєш автолейаути, працюєш із базовими компонентами, утеплюєш макети простими анімаціями. Твоє портфоліо містить 3–5 проєктів: адаптивний макет лендингу, редизайн невеликого додатка чи простий UI-kit. Ти вмієш пояснити, чому вибрав таку колірну гаму або чому встановив певну відстань між елементами. "
        "Все ще виправляєшся: тобі можуть підказувати оптимізувати зображення, дотримуватися гайдлайнів з контрастності, але загалом твої рішення приймають команди без серйозних зауважень. У спілкуванні з розробниками іноді виникають труднощі: не завжди пам’ятаєш особливості верстки, але вже знаєш базові HTML- і CSS-огріхи. Рекрутери бачать твій середній досвід: ти розумієш адаптивність, готовий працювати в команді, але все ще навчаєшся самоорганізації та тайм-менеджменту. Твої завдання на роботі: опрацьовувати готові прототипи, запускати невеликі A/B-тести, готувати прості клієнтські презентації. Щоб перейти на Middle-рівень, потрібно почати вести власний мікродизайн-проект: скласти невелику дизайн-систему, пропрацювати UX-дослідження для хоча б одного кейсу та навчитися наводити аргументи «під бізнес-задачі».,",
    ],
    "Middle": [
        "У тебе вже є 2–3 роки досвіду в дизайні: ти створював нескладні дизайн-системи для стартапів або підтримував великі UI-кити. Володієш автолейаутизованими компонентами, типографічними шкалами і розумієш принципи доступності (WCAG). Твоє портфоліо демонструє повні проєктні цикли: від брифу з клієнтом і user-research до прототипування та передачі макетів розробникам. Ти можеш самостійно проводити інтерв’ю з користувачами на рівні базових JTBD-методів, аналізувати результати, формувати гіпотези та вимірювати ефективність рішень. Команди дослухаються до твоїх порад: ти пропонуєш оптимізації, знижуєш ризики багів на етапі розробки та забезпечуєш узгодженість UI у всіх екосистемах продукту. Твоя роль уже включає комунікацію з продакт-менеджерами: ти вмієш «перекладати» бізнес-вимоги в ядро UX-концепції й правильно розставляти пріоритети. На цьому етапі ти виступаєш також наставником для молодших колег: перевіряєш їх макети, даєш фідбек."
        "Щоб вийти на Middle+ — потрібно почати впроваджувати невеликі R&D-задачі: досліджувати нові інструменти, запускати A/B-тести дизайну, пропонувати варіанти оптимізації флоу, створювати невеликі внутрішні гайди для команди.",
    ],
    "Middle+": [
        "Твій досвід сягає 4–5 років, ти вже брав участь у двох-трьох великих проєктах, де відповідав спочатку за створення UI-компонентів, а тепер навіть за координацію роботи інших Middle-дизайнерів. Ти не лише розробляєш дизайн-системи, а й керуєш «end-to-end» процесом: складаєш технічні специфікації, регламентуєш правила верстки, організовуєш QA-перевірки та адаптивне тестування. Твій портфоліо включає кейси з мультикейсовим UX-дослідженням, ти замовляєш і опрацьовуєш інтерв’ю з аудиторією, аналізуєш кількісні метрики (ми травики, конверсія, retention) й пропонуєш зміни на основі даних. В команді ти вже предметно впливаєш на рішення бізнес-рівня: обговорюєш пріоритети фічей із продуктовою командою, узгоджуєш технічні обмеження та вплив дизайну на метрики. Тебе залучають до планування roadmap-у, відстоюєш UX-цінність перед CTO. Дизайн-директори та HR-менеджери розглядають тебе як кандидата на позицію Senior — ти періодично ведеш невеликі воркшопи для новачків, формуєш чек-лісти та шаблони для швидкої розробки.",
        "Щоб стати Senior, варто почати керувати невеликими командами й брати на себе відповідальність за результати MVP із мінімальними координаційними втратами.",
    ],
    "Senior": [
        "На твоєму рахунку 6–8 років досвіду в індустрії: ти побудував чи значно розширив щонайменше одну масштабну дизайн-систему для великої компанії. Ти очолюєш команду з 3–5 Middle-дизайнерів, проводиш щотижневі one-on-one, оцінюєш ефективність процесів, задаєш KPI для розробників і дизайнерів. Ти тісно працюєш із C-level: погоджуєш стратегії розвитку продукту, формуєш план релізів і дизайн-тасків, складаєш roadmap дизайну на півроку і рік. Твої рішення значно впливають на бізнес-метрики: ти проєктуєш флоу для збільшення конверсій, зниження churn-у. Портфоліо — це не просто роботи, а повні кейси з «метрики до реалізації», де ти керував процесом від user-research до post-launch-аналізу. Тебе цінують за експертизу в побудові дизайн-менторингу, проведенні тренінгів для команди, стандартизації процесів між відділами. ",
        "Щоб вийти на рівень Lead / Senior+, потрібно почати брати участь у формуванні дизайн-стратегії компанії в цілому: розробляти guidelines для всіх продуктів, координувати крос-функціональні ініціативи, впроваджувати інновації (machine learning в UX, voice-интерфейси тощо), а також будувати корпоративну культуру дизайну.",
    ],
    "Lead / Senior+": [
        "Ти — архітектор дизайн-стратегії великої організації. Маєш за плечима 8–10+ років досвіду і керував командою 10–15 дизайнерів, UI/UX-дослідників та інженерів. Твоє портфоліо — це трансформація продуктів на рівні enterprise: ти визначав roadmap, брав участь у створенні мультикультурних дизайнів для ринків Європи, США та Азії. Ти прокладаєш шлях інноваціям: відпочатку створюєш R&D-подрозділ, впроваджуєш методології Design Thinking на рівні компанії, формуєш «дизайн-центр компетенцій». Як Lead, ти відповідаєш за довгостроковий розвиток дизайну, менеджиш співпрацю з маркетингом, аналітикою й стейкхолдерами. Твої рішення визначають тональність бренду, формують customer journey для десятків мільйонів користувачів. Для HR-менеджерів і топ-менеджерів ти — уособлення експертизи: саме тебе запрошують на панелі конференцій, ти читаєш лекції з продуктивності команд, кураторства та UI/UX-інновацій. Твоє завдання — не лише генерувати креатив, а й трансформувати культуру компанії так, щоб дизайн став конкурентною перевагою.",
    ],
}

# Banner
INTRO_PHOTO = Path(__file__).parent / "assets" / "intro.jpg"
INTRO_TEXT = (
    "<b>Що вміє цей бот?</b>\n"
    "Цей тест дасть вам приблизну оцінку вашого рівня та орієнтир вилки ЗП на ринку України. "
    "Кожна рекомендація побудована на відкритих вимогах вакансій та статистиці галузі.\n\n"
    "Натисніть «РОЗПОЧАТИ ТЕСТ» — і дізнайтеся свій результат та отримаєте невеликий чек‑лист із порадами."
)

# Questions
QUESTIONS = [
    ("Як часто вам повертають правки дизайну?",
     ["Замовникам часто не подобається", "Іноді приходять помірні правки", "Правки мінімальні", "Зазвичай без правок"],
     [1, 2, 3, 4]),
    ("Наскільки чітко ви пояснюєте свої дизайн-рішення?",
     ["Не вмію пояснювати", "Пояснюю не завжди зрозуміло", "Мене розуміють без проблем", "Чітко передаю ідеї"],
     [1, 2, 3, 4]),
    ("Як би ви оцінили свій рівень роботи у Figma?",
     ["Початківець", "Впевнено працюю з базовим функціоналом", "Володію автолейаутами й компонентами", "Експерт і наставник для інших"],
     [1, 2, 3, 4]),
    ("Як ви організовуєте простір і сітку в макеті?",
     ["Інтуїтивно вирівнюю елементи", "Використовую готові гідлайни", "Створюю власні системи сіток", "Оптимізую сітку для будь-яких форматів"],
     [1, 2, 3, 4]),
    ("Як ви підбираєте кольорову палітру для проєкту?",
     ["Обираю одну домінантну", "Користуюсь готовими шаблонами", "Створюю корпоративні палітри", "Враховую WCAG і токенізую кольори"],
     [1, 2, 3, 4]),
    ("Який ваш досвід створення адаптивних інтерфейсів?",
     ["Лише дизайн мобільних екранів", "Працюю з мобайлом і десктопом", "Створював адаптивні системи для різних платформ", "Пишу код для різних дисплеїв"],
     [1, 2, 3, 4]),
    ("Як ви працюєте з типографікою?",
     ["Застосовую базові налаштування шрифтів", "Слідую готовим масштабам", "Створюю власні шкали та лінійки", "Роблю оптичну корекцію і токенізую"],
     [1, 2, 3, 4]),
    ("Чи маєте ви досвід роботи з дизайн-системами?",
     ["Ніколи не працював", "Застосовував готові UI-кити", "Розширював існуючі дизайн-системи", "Створював масштабні дизайн-системи з нуля"],
     [1, 2, 3, 4]),
    ("Як ви збираєте та аналізуєте фідбек від користувачів?",
     ["Ігнорую коментарі", "Обробляю хаотично", "Систематично збираю й аналізую", "Використовую для постійного вдосконалення"],
     [1, 2, 3, 4]),
    ("Якими інструментами прототипування ви користуєтесь?",
     ["Не прототипую", "Використовую базові інструменти", "Створюю інтерактивні прототипи", "Владную складні сценарії прототипів"],
     [1, 2, 3, 4]),
    ("Як ви тестуєте свої дизайн-рішення?",
     ["Не тестую", "Перевіряю на друзях", "Провожу базові юзер-тести", "Впроваджую комплексні дослідження"],
     [1, 2, 3, 4]),
    ("Як ви управляєте дедлайнами та пріоритетами?",
     ["Часто зриваю терміни", "Іноді встигаю", "Зазвичай укладаюся", "Гарантовано завершую раніше"],
     [1, 2, 3, 4]),
    ("Як ви співпрацюєте з розробниками?",
     ["Уникаю технічних деталей", "Обговорюю тільки найнеобхідніше", "Підтримую постійний діалог", "Гармонійно інтегрую дизайн у код"],
     [1, 2, 3, 4]),
    ("Як ви враховуєте доступність (a11y) у своїх проєктах?",
     ["Не враховую", "Перевіряю контраст", "Застосовую базові правила", "Глибоко інтегрую доступність у дизайн-систему"],
     [1, 2, 3, 4]),
    ("Який у вас досвід проведення UX-досліджень?",
     ["Не проводив", "Пробував коридорні тести", "Провів декілька інтерв'ю", "Виконав крупні дослідження з аналітикою"],
     [1, 2, 3, 4]),
    ("Як ви вирішуєте конфлікти в команді?",
     ["Уникаю спілкування", "Намагаюся не загострювати", "Шукаю конструктивні рішення", "Медіую і знаходжу компроміс"],
     [1, 2, 3, 4]),
    ("Як ви адаптуєте дизайн під різні платформи?",
     ["Дизайн для однієї платформи", "Переношу елементи вручну", "Створюю адаптивні макети", "Розробляю кросплатформні рішення"],
     [1, 2, 3, 4]),
    ("Як ви оновлюєте своє портфоліо?",
     ["Додаю рідко", "Раз на рік оновлюю", "Після кожного проєкту", "Постійно слідкую і поповнюю"],
     [1, 2, 3, 4]),
    ("Як ви презентуєте дизайнерські рішення?",
     ["Просто показую макети", "Пояснюю поверхово", "Аргументую кожен вибір", "Вмію переконувати аудиторію"],
     [1, 2, 3, 4]),
    ("Як ви слідкуєте за новими трендами у дизайні?",
     ["Не стежу", "Читаю іноді блоги", "Регулярно вивчаю новинки", "Генерую власні тренди"],
     [1, 2, 3, 4]),
    ("Як ви поєднуєте креативність і бізнес-цілі?",
     ["Фокусуюся на красі", "Іноді враховую цілі", "Балансую між ними", "Роблю дизайн, що продає"],
     [1, 2, 3, 4]),
    ("Як ви застосовуєте дизайнерське мислення у вашій роботі?",
     ["Не знайомий з концепцією",
      "Слухав, але рідко застосовую",
      "Регулярно використовую в проектах",
      "Навчаю колег та впроваджую практику"],
     [1, 2, 3, 4]),
]

# Levels
LEVELS = [
    (1.00, 1.50, "Начинающий (ниже Junior)",  400,  600),
    (1.51, 2.20, "Junior",                    600,  900),
    (2.21, 2.80, "Middle",                    900, 1600),
    (2.81, 3.30, "Middle+",                  1600, 2400),
    (3.31, 3.70, "Senior",                   2400, 3200),
    (3.71, 4.00, "Lead / Senior+",           3200, 4500),
]

# States
WAIT_START, ASKING, CHECK_SUBSCRIPTION = range(3)

# Function to check subscription
async def check_subscription(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    """Проверяет подписку пользователя на канал"""
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except BadRequest as e:
        logging.warning(f"Ошибка при проверке подписки: {e}")
        return False
    except Exception as e:
        logging.error(f"Неожиданная ошибка при проверке подписки: {e}")
        return False

# Function to clear user data
def clear_user_data(context: ContextTypes.DEFAULT_TYPE):
    """Очищает данные пользователя"""
    context.user_data.clear()

# /start handler - теперь всегда сбрасывает состояние
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Очищаем все данные пользователя при каждом старте
    clear_user_data(context)
    btn = InlineKeyboardButton("▶ РОЗПОЧАТИ ТЕСТ", callback_data="begin")
    markup = InlineKeyboardMarkup([[btn]])
    if INTRO_PHOTO.exists():
        with INTRO_PHOTO.open("rb") as photo:
            await update.message.reply_photo(
                photo=photo,
                caption=INTRO_TEXT,
                parse_mode="HTML",
                reply_markup=markup,
            )
    else:
        await update.message.reply_text(INTRO_TEXT, parse_mode="HTML", reply_markup=markup)
    return WAIT_START

# Begin quiz with subscription check
async def begin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    user_id = update.effective_user.id
    logging.info(f"Проверяем подписку для пользователя {user_id}")
    is_subscribed = await check_subscription(context, user_id)
    logging.info(f"Результат проверки подписки: {is_subscribed}")
    if not is_subscribed:
        subscribe_btn = InlineKeyboardButton("🔔 Підписатися на канал", url=CHANNEL_LINK)
        check_btn = InlineKeyboardButton("✅ Я підписався", callback_data="check_sub")
        markup = InlineKeyboardMarkup([[subscribe_btn], [check_btn]])
        subscription_text = (
            "❗️ Для проходження тесту необхідно підписатися на наш канал!\n\n"
            "На каналі ви знайдете:\n"
            "• Поради щодо розвитку кар'єри в дизайні\n"
            "• Корисні інструменты для роботи\n"
            "• Актуальні тренди та кейси\n\n"
            "Після підписки натисніть кнопку нижче для продовження."
        )
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=subscription_text,
            reply_markup=markup,
            parse_mode="HTML"
        )
        return CHECK_SUBSCRIPTION
    else:
        context.user_data["q"] = 0
        context.user_data["scores"] = []
        return await ask_question(update, context)

# Check subscription callback
async def check_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    user_id = update.effective_user.id
    logging.info(f"Повторная проверка подписки для пользователя {user_id}")
    is_subscribed = await check_subscription(context, user_id)
    logging.info(f"Результат повторной проверки: {is_subscribed}")
    if not is_subscribed:
        # Показываем сообщение с предупреждением
        subscribe_btn = InlineKeyboardButton("🔔 Підписатися на канал", url=CHANNEL_LINK)
        check_btn = InlineKeyboardButton("✅ Перевірити підписку", callback_data="check_sub")
        markup = InlineKeyboardMarkup([[subscribe_btn], [check_btn]])
        warning_text = (
            "👁️ <b>BigBro слідкує і не бачить підписку!</b> 👁️\n\n"
            "❌ Ви ще не підписані на мій канал.\n"
            "Будь ласка, підпишіться і потім натисніть кнопку перевірки.\n\n"
            "🔍 <i>Система автоматично перевіряє вашу підписку через Telegram API</i>"
        )
        try:
            await update.callback_query.edit_message_text(
                text=warning_text,
                reply_markup=markup,
                parse_mode="HTML"
            )
        except:
            # Если не удалось отредактировать, отправляем новое сообщение
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=warning_text,
                reply_markup=markup,
                parse_mode="HTML"
            )
        return CHECK_SUBSCRIPTION
    else:
        await update.callback_query.answer("✅ Дякую за підписку! Починаємо тест.")
        context.user_data["q"] = 0
        context.user_data["scores"] = []
        try:
            await update.callback_query.message.delete()
        except:
            pass
        return await ask_question(update, context)

# Ask question
async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    idx = context.user_data["q"]
    question, answers, _ = QUESTIONS[idx]
    labels = ["A", "B", "C", "D"]
    text = f"*{idx+1} / {len(QUESTIONS)}*\n{question}\n\n"
    for i, ans in enumerate(answers):
        text += f"{labels[i]}. {ans}\n"

    btn_row = [InlineKeyboardButton(labels[i], callback_data=str(i)) for i in range(len(answers))]
    back_btn = InlineKeyboardButton("Назад", callback_data="prev")
    markup = InlineKeyboardMarkup([btn_row, [back_btn]])

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        reply_markup=markup,
        parse_mode="Markdown"
    )
    return ASKING

# Функция для анимации загрузки результата
async def show_loading_animation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает анимацию загрузки результата"""
    loading_frames = [
        "🔮 Считаем твой результат\n\n[⚪⚪⚪⚪⚪⚪⚪⚪⚪⚪] 0%",
        "🔮 Считаем твой результат\n\n[🔵⚪⚪⚪⚪⚪⚪⚪⚪⚪] 10%",
        "🔮 Считаем твой результат\n\n[🔵🔵⚪⚪⚪⚪⚪⚪⚪⚪] 20%",
        "🔮 Считаем твой результат\n\n[🔵🔵🔵⚪⚪⚪⚪⚪⚪⚪] 30%",
        "🔮 Считаем твой результат\n\n[🔵🔵🔵🔵⚪⚪⚪⚪⚪⚪] 40%",
        "🔮 Считаем твой результат\n\n[🔵🔵🔵🔵🔵⚪⚪⚪⚪⚪] 50%",
        "🔮 Считаем твой результат\n\n[🔵🔵🔵🔵🔵🔵⚪⚪⚪⚪] 60%",
        "🔮 Считаем твой результат\n\n[🔵🔵🔵🔵🔵🔵🔵⚪⚪⚪] 70%",
        "🔮 Считаем твой результат\n\n[🔵🔵🔵🔵🔵🔵🔵🔵⚪⚪] 80%",
        "🔮 Считаем твой результат\n\n[🔵🔵🔵🔵🔵🔵🔵🔵🔵⚪] 90%",
        "🔮 Считаем твой результат\n\n[🔵🔵🔵🔵🔵🔵🔵🔵🔵🔵] 100%",
        "✨ Результат готов! ✨"
    ]
    # Отправляем первый кадр
    loading_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=loading_frames[0]
    )
    # Анимация прогресс-бара
    for frame in loading_frames[1:]:
        await asyncio.sleep(0.3)  # Задержка между кадрами
        try:
            await loading_message.edit_text(frame)
        except:
            # Если не удалось отредактировать, продолжаем
            pass
    # Удаляем сообщение с анимацией через секунду
    await asyncio.sleep(1)
    try:
        await loading_message.delete()
    except:
        pass

# Handle answer
async def answer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    # Delete the previous question message so user cannot re-answer it
    try:
        await update.callback_query.message.delete()
    except Exception:
        pass
    choice = int(update.callback_query.data)
    q_i = context.user_data["q"]
    _, _, score_map = QUESTIONS[q_i]
    context.user_data["scores"].append(score_map[choice])
    context.user_data["q"] += 1

    if context.user_data["q"] < len(QUESTIONS):
        return await ask_question(update, context)

    # Показываем анимацию загрузки перед результатами
    await show_loading_animation(update, context)

    total = sum(context.user_data["scores"])
    avg = total / len(QUESTIONS)
    title = None
    salary = None
    for low, high, lvl, low_sal, high_sal in LEVELS:
        if low <= avg <= high:
            title = lvl
            salary = f"${low_sal:,} – ${high_sal:,} /мес (нетто)"
            break

    msg = (
        f"**Бали:** {total} (середній {avg:.2f})\n"
        f"**Рівень:** {title}\n"
        f"**Діапазон ЗП:** {salary}"
    )

    recs = RECOMMENDATIONS.get(title, [])
    if recs:
        msg += "\n\n**Рекомендації для розвитку:**"
        for i, r in enumerate(recs, 1):
            msg += f"\n{i}. {r}"

    # Відправляємо результат окремим повідомленням з оформленням
    result_header = "🎉 *Ваш результат* 🎉"
    formatted_msg = f"{result_header}\n\n{msg}"
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=formatted_msg,
        parse_mode="Markdown"
    )

    await asyncio.sleep(5)

    subscribe_btn = InlineKeyboardButton("🔔 Підписатися на канал", url=CHANNEL_LINK)
    linkedin_btn = InlineKeyboardButton("LinkedIn", url="https://www.linkedin.com/in/bohdan-svitlyk-960481a0/")
    instagram_btn = InlineKeyboardButton("Instagram", url="https://www.instagram.com/bogdan_svit?igsh=dDdqOXNzOTQ5cHkw")
    markup = InlineKeyboardMarkup([
        [subscribe_btn],
        [linkedin_btn, instagram_btn]
    ])

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            "<b>Дякую за проходження тесту!</b>\n\n"
            "На нашому каналі ви знайдете:\n"
            "• поради щодо розвитку кар’єри;\n"
            "• інструменти, що допомагають у роботі та пошуку роботи;\n"
            "• актуальні тренди та кейси.\n\n"
            "Підпишіться, щоб не пропустити нові оновлення!\n\n"
            "<b>Корисні матеріали за посиланнями:</b>\n"
            "🔹 <a href=\"https://t.me/digitaI_age/11\">Десять порад, які я б собі дав на початку кар’єри</a>\n"
            "🔹 <a href=\"https://t.me/digitaI_age/26\">Шаблон для базових UX-опитувань</a>\n"
            "🔹 <a href=\"https://t.me/digitaI_age/55\">“ChatGPT для вебдизайнерів”</a>\n"
            "🔹 <a href=\"https://t.me/digitaI_age/68\">PDF-гайд «UI-дизайн з нуля»</a>\n"
            "🔹 <a href=\"https://t.me/digitaI_age/69\">Шаблон портфоліо в Notion</a>\n"
            "🔹 <a href=\"https://t.me/digitaI_age/74\">Гайд для тих, хто хоче ввірватися в UX-дизайн</a>\n"
            "🔹 <a href=\"https://t.me/digitaI_age/77\">Простий гайд українською: Figma Grid</a>\n"
            "🔹 <a href=\"https://t.me/digitaI_age/87\">Як дизайнеру вирости до нового рівня: 7 кроків до успіху</a>\n"
            "🔹 <a href=\"https://t.me/digitaI_age/99\">18 практичних ідей (промптів) для використання AI у дизайні</a>\n\n"
            "⸻\n"
            "Підпишіться на канал, щоб не пропустити наступні гайди, шаблони та кейси!"
        ),
        reply_markup=markup,
        parse_mode="HTML"
    )
    return ConversationHandler.END

# Handle "Назад"
async def prev_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    # Delete the current question message before showing the previous one
    try:
        await update.callback_query.message.delete()
    except Exception:
        pass
    if context.user_data["q"] > 0:
        context.user_data["q"] -= 1
        context.user_data["scores"].pop()
    return await ask_question(update, context)

# Cancel
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_user_data(context)
    await update.message.reply_text("Опитування скасовано.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Обработчик для любых сообщений вне состояния разговора
async def handle_unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает сообщения, которые приходят вне conversation handler"""
    await update.message.reply_text(
        "Привіт! Щоб почати тест, натисніть /start",
        reply_markup=ReplyKeyboardRemove()
    )

# Обработчик ошибок
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает ошибки"""
    logging.error(f"Exception while handling an update: {context.error}")
    # Если это обновление от пользователя, очищаем его данные
    if isinstance(update, Update) and update.effective_user:
        clear_user_data(context)

# Main
async def health(request):
    return aiohttp.web.Response(text="OK")

async def start_health_server():
    if aiohttp is None:
        return
    app = aiohttp.web.Application()
    app.router.add_get('/health', health)
    runner = aiohttp.web.AppRunner(app)
    await runner.setup()
    site = aiohttp.web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()

async def main():
    application = Application.builder().token(TOKEN).build()

    # Conversation handler
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAIT_START: [CallbackQueryHandler(begin_callback, pattern="^begin$")],
            ASKING: [
                CallbackQueryHandler(answer_callback, pattern="^[0-9]$"),
                CallbackQueryHandler(prev_callback, pattern="^prev$"),
            ],
            CHECK_SUBSCRIPTION: [
                CallbackQueryHandler(check_subscription_callback, pattern="^check_sub$")
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )
    application.add_handler(conv)
    application.add_handler(CommandHandler("start", start))

    await application.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.get_event_loop().create_task(main())
    asyncio.get_event_loop().run_forever()
