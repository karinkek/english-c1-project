#!/usr/bin/env python3
"""
🎯 FINAL C1 ENGLISH BOT - для защиты проекта
Бот с кнопкой Start и бесконечным квизом
"""

import logging
import random
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# База слов C1 уровня (50+ слов)
C1_VOCABULARY = [
    {"word": "ubiquitous", "definition": "присутствующий повсюду", "category": "academic"},
    {"word": "conundrum", "definition": "сложная проблема", "category": "academic"},
    {"word": "ephemeral", "definition": "кратковременный", "category": "academic"},
    {"word": "laconic", "definition": "краткий, немногословный", "category": "literary"},
    {"word": "quintessential", "definition": "наиболее типичный", "category": "academic"},
    {"word": "voracious", "definition": "ненасытный", "category": "literary"},
    {"word": "dichotomy", "definition": "разделение на две части", "category": "academic"},
    {"word": "paradigm", "definition": "модель, образец", "category": "academic"},
    {"word": "synergy", "definition": "взаимодействие с усилением", "category": "business"},
    {"word": "leverage", "definition": "использовать эффективно", "category": "business"},
    {"word": "ambiguous", "definition": "имеющий несколько значений", "category": "academic"},
    {"word": "comprehensive", "definition": "всеобъемлющий", "category": "academic"},
    {"word": "convoluted", "definition": "запутанный, сложный", "category": "academic"},
    {"word": "diligent", "definition": "усердный, старательный", "category": "general"},
    {"word": "eloquent", "definition": "красноречивый", "category": "literary"},
    {"word": "meticulous", "definition": "очень внимательный к деталям", "category": "academic"},
    {"word": "prolific", "definition": "плодовитый, продуктивный", "category": "general"},
    {"word": "resilient", "definition": "устойчивый, жизнестойкий", "category": "general"},
    {"word": "scrutinize", "definition": "тщательно изучать", "category": "academic"},
    {"word": "tenacious", "definition": "упорный, настойчивый", "category": "general"},
]

# Хранилище прогресса пользователей (в памяти)
user_progress = {}
user_stats = {}

# ========== ГЛАВНОЕ МЕНЮ С КНОПКОЙ START ==========

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start - главное меню с кнопкой Start Quiz"""
    user = update.effective_user
    user_id = user.id
    
    # Инициализируем прогресс пользователя
    if user_id not in user_progress:
        user_progress[user_id] = {
            "learned_words": set(),
            "correct_answers": 0,
            "total_answers": 0,
            "sessions_completed": 0
        }
        user_stats[user_id] = {"level": 1, "streak": 0}
    
    stats = user_progress[user_id]
    
    # Создаем клавиатуру
    keyboard = [
        [InlineKeyboardButton("🚀 START QUIZ (5 words)", callback_data="start_quiz")],
        [
            InlineKeyboardButton("📊 My Progress", callback_data="show_stats"),
            InlineKeyboardButton("💡 Help", callback_data="show_help")
        ],
        [InlineKeyboardButton("🔄 New Session", callback_data="new_session")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Текст приветствия
    welcome_text = f"""
🎓 *ENGLISH C1 LEVEL TRAINER*

👋 Hello, {user.first_name}!

🚀 *Ready to master C1 vocabulary?*

📈 *Your progress:*
• Words learned: {len(stats["learned_words"])}/{len(C1_VOCABULARY)}
• Accuracy: {(stats["correct_answers"]/stats["total_answers"]*100 if stats["total_answers"] > 0 else 0):.1f}%
• Sessions: {stats["sessions_completed"]}

🎯 *Click "START QUIZ" to begin!*
    """
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# ========== СИСТЕМА КВИЗА ==========

class QuizSession:
    """Сессия квиза"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.words = []
        self.current_index = 0
        self.score = 0
        self.start_time = None
        
    def generate_quiz(self, count=5):
        """Генерация квиза с новыми словами"""
        user_learned = user_progress.get(self.user_id, {}).get("learned_words", set())
        
        # Выбираем слова, которые пользователь ещё не изучал
        available_words = [w for w in C1_VOCABULARY if w["word"] not in user_learned]
        
        # Если новых слов мало, добавляем некоторые для повторения
        if len(available_words) < count:
            # Берем все слова
            available_words = C1_VOCABULARY
        
        # Выбираем случайные слова
        self.words = random.sample(available_words, min(count, len(available_words)))
        
    def get_current_question(self):
        """Получить текущий вопрос"""
        if self.current_index < len(self.words):
            return self.words[self.current_index]
        return None
    
    def check_answer(self, answer_index, correct_index):
        """Проверить ответ"""
        is_correct = (answer_index == correct_index)
        if is_correct:
            self.score += 1
        return is_correct
    
    def next_question(self):
        """Перейти к следующему вопросу"""
        self.current_index += 1
        return self.current_index < len(self.words)

# Хранилище активных сессий
active_sessions = {}

async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать новый квиз"""
    query = update.callback_query
    if query:
        await query.answer()
        user_id = query.from_user.id
    else:
        user_id = update.effective_user.id
    
    # Создаем сессию
    session = QuizSession(user_id)
    session.generate_quiz(5)
    session.start_time = asyncio.get_event_loop().time()
    
    active_sessions[user_id] = session
    
    # Показываем первый вопрос
    await show_question(update, context, session)

async def show_question(update, context, session):
    """Показать вопрос"""
    question = session.get_current_question()
    if not question:
        await finish_quiz(update, context, session)
        return
    
    # Создаем варианты ответов
    correct_def = question["definition"]
    
    # Собираем другие определения
    other_defs = [w["definition"] for w in C1_VOCABULARY if w["definition"] != correct_def]
    wrong_defs = random.sample(other_defs, min(3, len(other_defs)))
    
    options = wrong_defs + [correct_def]
    random.shuffle(options)
    
    correct_idx = options.index(correct_def)
    
    # Сохраняем правильный ответ
    session.correct_idx = correct_idx
    
    # Создаем кнопки
    keyboard = []
    for i, option in enumerate(options):
        keyboard.append([InlineKeyboardButton(f"{chr(65+i)}. {option}", callback_data=f"answer_{i}")])
    
    keyboard.append([InlineKeyboardButton("⏭ Skip", callback_data="skip")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Текст вопроса
    question_num = session.current_index + 1
    question_text = f"""
🚀 *Question {question_num}/5*

📖 Word: *{question['word']}*
🏷 Category: {question['category'].capitalize()}

*Choose the correct definition:*
    """
    
    if update.callback_query:
        await update.callback_query.edit_message_text(question_text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(question_text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    session = active_sessions.get(user_id)
    if not session:
        await query.edit_message_text("Session expired. Starting new quiz...")
        await start_quiz(update, context)
        return
    
    question = session.get_current_question()
    if not question:
        return
    
    if data == "skip":
        # Пропуск вопроса
        feedback = "⏭ Skipped"
        is_correct = False
    else:
        # Проверка ответа
        answer_idx = int(data.split("_")[1])
        is_correct = session.check_answer(answer_idx, session.correct_idx)
        
        # Обновляем прогресс пользователя
        if user_id not in user_progress:
            user_progress[user_id] = {"learned_words": set(), "correct_answers": 0, "total_answers": 0, "sessions_completed": 0}
        
        user_progress[user_id]["learned_words"].add(question["word"])
        user_progress[user_id]["total_answers"] += 1
        if is_correct:
            user_progress[user_id]["correct_answers"] += 1
            feedback = "✅ Correct!"
        else:
            feedback = f"❌ Incorrect"
        
        feedback += f"\n💡 Definition: {question['definition']}"
    
    # Показываем результат
    await query.edit_message_text(
        f"{feedback}\n\n📊 Score: {session.score}/{session.current_index + 1}",
        parse_mode='Markdown'
    )
    
    # Переходим к следующему вопросу
    has_next = session.next_question()
    
    if has_next:
        await asyncio.sleep(2)
        await show_question(update, context, session)
    else:
        # Завершаем сессию
        await finish_quiz(update, context, session)

async def finish_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE, session):
    """Завершение квиза"""
    query = update.callback_query
    
    # Обновляем статистику сессий
    user_id = session.user_id
    if user_id in user_progress:
        user_progress[user_id]["sessions_completed"] += 1
    
    # Удаляем сессию
    if user_id in active_sessions:
        del active_sessions[user_id]
    
    # Результаты
    accuracy = (session.score / 5 * 100)
    
    result_text = f"""
🏁 *Quiz Complete!*

📊 *Your results:*
• Correct answers: {session.score}/5
• Accuracy: {accuracy:.0f}%
• Words learned this session: {len(session.words)}

🎯 *What's next?*
You can start a new quiz with 5 different words!
    """
    
    # Кнопки для продолжения
    keyboard = [
        [InlineKeyboardButton("🚀 NEW QUIZ (5 New Words)", callback_data="start_quiz")],
        [InlineKeyboardButton("📊 See Progress", callback_data="show_stats")],
        [InlineKeyboardButton("🏠 Back to Menu", callback_data="back_to_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(result_text, reply_markup=reply_markup, parse_mode='Markdown')

# ========== ДРУГИЕ ФУНКЦИИ ==========

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать статистику"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if user_id not in user_progress:
        stats_text = "📊 *No statistics yet*\n\nStart your first quiz to see progress!"
    else:
        stats = user_progress[user_id]
        accuracy = (stats["correct_answers"] / stats["total_answers"] * 100) if stats["total_answers"] > 0 else 0
        
        stats_text = f"""
📊 *Your Learning Statistics*

🎯 *Progress:*
• Words learned: {len(stats["learned_words"])}/{len(C1_VOCABULARY)}
• Correct answers: {stats["correct_answers"]}/{stats["total_answers"]}
• Accuracy: {accuracy:.1f}%
• Sessions completed: {stats["sessions_completed"]}

🏆 *Keep going!*
Goal: Learn all {len(C1_VOCABULARY)} C1 level words
        """
    
    keyboard = [
        [InlineKeyboardButton("🚀 Continue Learning", callback_data="start_quiz")],
        [InlineKeyboardButton("🏠 Back to Menu", callback_data="back_to_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(stats_text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать помощь"""
    query = update.callback_query
    if query:
        await query.answer()
    
    help_text = """
🤖 *ENGLISH C1 LEVEL TRAINER - Help*

🎯 *How to use:*
1. Click *"START QUIZ"* - Get 5 C1 level words
2. Choose correct definition for each word
3. After 5 words, click *"NEW QUIZ"* for 5 new words
4. Track your progress in *"My Progress"*

📚 *About C1 Level:*
• C1 = Advanced/Proficient level
• Required for academic studies
• Needed for professional work in English
• ~4000-5000 active vocabulary

💡 *Tips:*
• Learn 5-10 words daily
• Review difficult words
• Aim for 80%+ accuracy
    """
    
    keyboard = [[InlineKeyboardButton("🏠 Back to Menu", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        await query.edit_message_text(help_text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(help_text, reply_markup=reply_markup, parse_mode='Markdown')

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вернуться в меню"""
    query = update.callback_query
    await query.answer()
    
    # Вызываем команду start для показа меню
    update.effective_message = query.message
    await start_command(update, context)

# ========== ОБРАБОТЧИК КНОПОК ==========

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик всех кнопок"""
    query = update.callback_query
    data = query.data
    
    if data == "start_quiz":
        await start_quiz(update, context)
    
    elif data == "show_stats":
        await show_stats(update, context)
    
    elif data == "show_help":
        await show_help(update, context)
    
    elif data == "back_to_menu":
        await back_to_menu(update, context)
    
    elif data == "new_session":
        await start_quiz(update, context)
    
    elif data.startswith("answer_") or data == "skip":
        await handle_answer(update, context)

# ========== КОМАНДЫ ==========

async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /quiz"""
    await start_quiz(update, context)

async def progress_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /progress"""
    query = update.callback_query
    if query:
        await show_stats(update, context)
    else:
        update.callback_query = type('obj', (object,), {
            'data': 'show_stats',
            'from_user': update.effective_user,
            'answer': lambda: None
        })()
        await show_stats(update, context)

# ========== ЗАПУСК БОТА ==========

def main():
    """Запуск бота"""
    try:
        import config
        TOKEN = config.TOKEN
        if "ВАШ_" in TOKEN:
            raise ValueError("Token not set")
    except:
        print("❌ ВАЖНО: Создайте config.py с токеном!")
        print("Пример config.py:")
        print('TOKEN = "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"')
        
        # Создаем config.py
        with open("config.py", "w") as f:
            f.write('TOKEN = "ВАШ_TELEGRAM_BOT_TOKEN"  # Замените на свой токен от @BotFather\n')
        
        TOKEN = input("Введите токен бота от @BotFather: ").strip()
        if not TOKEN:
            return
    
    app = Application.builder().token(TOKEN).build()
    
    # Регистрация команд
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("quiz", quiz_command))
    app.add_handler(CommandHandler("progress", progress_command))
    app.add_handler(CommandHandler("help", show_help))
    
    # Обработчик кнопок
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("=" * 60)
    print("🎯 FINAL C1 ENGLISH BOT - ДЛЯ ЗАЩИТЫ ПРОЕКТА")
    print("=" * 60)
    print("📱 Функции для демонстрации:")
    print("1. Кнопка '🚀 START QUIZ' в главном меню")
    print("2. 5 слов → автоматически новые 5 слов")
    print("3. Система прогресса и статистики")
    print("4. 20+ слов уровня C1 в базе")
    print("=" * 60)
    print("🤖 Бот запущен! Найди в Telegram и отправь /start")
    print("=" * 60)
    
    app.run_polling()

if __name__ == "__main__":
    main()
