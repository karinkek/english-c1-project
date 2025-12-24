#!/usr/bin/env python3
"""
🎯 FIXED C1 ENGLISH BOT - Исправлена ошибка с Back to Menu
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

# База слов (упрощенная версия)
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

# Хранилище прогресса
user_progress = {}
active_sessions = {}

# ========== ГЛАВНОЕ МЕНЮ ==========

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    
    # Инициализируем прогресс
    if user.id not in user_progress:
        user_progress[user.id] = {
            "learned": set(),
            "correct": 0,
            "total": 0,
            "sessions": 0
        }
    
    stats = user_progress[user.id]
    learned = len(stats["learned"])
    accuracy = (stats["correct"] / stats["total"] * 100) if stats["total"] > 0 else 0
    
    keyboard = [
        [InlineKeyboardButton("🚀 START QUIZ (5 words)", callback_data="start_quiz")],
        [
            InlineKeyboardButton("📊 My Stats", callback_data="show_stats"),
            InlineKeyboardButton("💡 Help", callback_data="show_help")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = f"""
🎓 *C1 ENGLISH TRAINER*

👋 *Welcome, {user.first_name}!*

📊 *Your Progress:*
• Words learned: {learned}/{len(C1_VOCABULARY)}
• Accuracy: {accuracy:.1f}%
• Sessions: {stats['sessions']}

🎯 *Click START QUIZ to begin!*
    """
    
    # Если это callback, редактируем сообщение
    if update.callback_query:
        await update.callback_query.edit_message_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

# ========== СИСТЕМА КВИЗА ==========

async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать квиз"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # Выбираем 5 случайных слов
    available_words = [w for w in C1_VOCABULARY]
    words = random.sample(available_words, min(5, len(available_words)))
    
    # Создаем сессию
    active_sessions[user_id] = {
        "words": words,
        "current": 0,
        "score": 0
    }
    
    await show_question(update, context, user_id)

async def show_question(update, context, user_id):
    """Показать вопрос"""
    session = active_sessions.get(user_id)
    if not session:
        return
    
    words = session["words"]
    current_idx = session["current"]
    
    if current_idx >= len(words):
        await finish_quiz(update, context, user_id)
        return
    
    word = words[current_idx]
    
    # Варианты ответов
    correct_def = word["definition"]
    all_defs = [w["definition"] for w in C1_VOCABULARY if w["definition"] != correct_def]
    wrong_defs = random.sample(all_defs, min(3, len(all_defs)))
    
    options = wrong_defs + [correct_def]
    random.shuffle(options)
    correct_idx = options.index(correct_def)
    
    # Сохраняем правильный ответ
    session["correct_idx"] = correct_idx
    active_sessions[user_id] = session
    
    # Кнопки
    keyboard = []
    for i, option in enumerate(options):
        keyboard.append([InlineKeyboardButton(f"{chr(65+i)}. {option}", callback_data=f"answer_{i}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Текст вопроса
    question_num = current_idx + 1
    question_text = f"""
🚀 *Question {question_num}/5*

📖 Word: *{word['word']}*

*Choose the correct definition:*
    """
    
    query = update.callback_query
    await query.edit_message_text(
        question_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    session = active_sessions.get(user_id)
    if not session:
        await query.edit_message_text("Starting new quiz...")
        await start_quiz(update, context)
        return
    
    words = session["words"]
    current_idx = session["current"]
    word = words[current_idx]
    
    # Проверяем ответ
    answer_idx = int(data.split("_")[1])
    correct_idx = session.get("correct_idx", 0)
    is_correct = (answer_idx == correct_idx)
    
    if is_correct:
        session["score"] += 1
        feedback = f"✅ *Correct!*"
    else:
        feedback = f"❌ *Incorrect*"
    
    # Обновляем прогресс
    if user_id not in user_progress:
        user_progress[user_id] = {"learned": set(), "correct": 0, "total": 0, "sessions": 0}
    
    user_progress[user_id]["learned"].add(word["word"])
    user_progress[user_id]["total"] += 1
    if is_correct:
        user_progress[user_id]["correct"] += 1
    
    await query.edit_message_text(
        f"{feedback}\n\n💡 Definition: {word['definition']}\n\n📊 Score: {session['score']}/{current_idx + 1}",
        parse_mode='Markdown'
    )
    
    # Следующий вопрос
    session["current"] += 1
    active_sessions[user_id] = session
    
    await asyncio.sleep(2)
    
    if session["current"] < len(words):
        await show_question(update, context, user_id)
    else:
        await finish_quiz(update, context, user_id)

async def finish_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id):
    """Завершение квиза"""
    session = active_sessions.get(user_id)
    if not session:
        return
    
    # Обновляем статистику сессий
    if user_id in user_progress:
        user_progress[user_id]["sessions"] += 1
    
    # Результаты
    score = session["score"]
    accuracy = (score / 5 * 100)
    
    stats = user_progress.get(user_id, {"learned": set(), "correct": 0, "total": 0})
    learned = len(stats["learned"])
    
    result_text = f"""
🏁 *Quiz Complete!*

📊 *Results:*
• Correct: {score}/5
• Accuracy: {accuracy:.0f}%

📈 *Overall Progress:*
• Words learned: {learned}/{len(C1_VOCABULARY)}
• Total accuracy: {(stats['correct']/stats['total']*100 if stats['total'] > 0 else 0):.1f}%
    """
    
    # Удаляем сессию
    if user_id in active_sessions:
        del active_sessions[user_id]
    
    # Кнопки
    keyboard = [
        [InlineKeyboardButton("🚀 NEW QUIZ (5 More Words)", callback_data="start_quiz")],
        [InlineKeyboardButton("📊 View Stats", callback_data="show_stats")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query = update.callback_query
    await query.edit_message_text(
        result_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# ========== ДРУГИЕ ФУНКЦИИ ==========

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать статистику"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if user_id not in user_progress:
        stats_text = "📊 *No statistics yet*\n\nStart your first quiz!"
    else:
        stats = user_progress[user_id]
        learned = len(stats["learned"])
        accuracy = (stats["correct"] / stats["total"] * 100) if stats["total"] > 0 else 0
        
        stats_text = f"""
📊 *Your Statistics*

🎯 *Progress:*
• Words learned: {learned}/{len(C1_VOCABULARY)}
• Correct answers: {stats['correct']}/{stats['total']}
• Accuracy: {accuracy:.1f}%
• Sessions: {stats['sessions']}

🏆 *Keep learning!*
        """
    
    keyboard = [
        [InlineKeyboardButton("🚀 Continue Learning", callback_data="start_quiz")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        stats_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать помощь"""
    query = update.callback_query
    await query.answer()
    
    help_text = """
🤖 *C1 ENGLISH TRAINER - Help*

🎯 *How to use:*
1. Click *"START QUIZ"* - Get 5 C1 level words
2. Choose correct definition for each word
3. After 5 words, click *"NEW QUIZ"* for 5 new words
4. Track progress in *"My Stats"*

📚 *About C1 Level:*
• Advanced English proficiency
• Academic & professional vocabulary
• Complex words and expressions

💡 *Tips:*
• Learn 5-10 words daily
• Review regularly
• Aim for 80%+ accuracy
    """
    
    keyboard = [[InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        help_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# ========== ОБРАБОТЧИК КНОПОК ==========

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопок - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    query = update.callback_query
    data = query.data
    
    if data == "start_quiz":
        await start_quiz(update, context)
    
    elif data == "show_stats":
        await show_stats(update, context)
    
    elif data == "show_help":
        await show_help(update, context)
    
    elif data == "back_to_menu":
        # ВАЖНО: Не изменяем update, а вызываем start_command напрямую
        await start_command(update, context)
    
    elif data.startswith("answer_"):
        await handle_answer(update, context)

# ========== КОМАНДЫ ==========

async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /quiz"""
    if update.callback_query:
        await start_quiz(update, context)
    else:
        # Если команда из текста, имитируем callback
        class FakeQuery:
            def __init__(self, user):
                self.from_user = user
                self.data = "start_quiz"
            
            async def answer(self):
                pass
        
        update.callback_query = FakeQuery(update.effective_user)
        await start_quiz(update, context)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /stats"""
    if update.callback_query:
        await show_stats(update, context)
    else:
        class FakeQuery:
            def __init__(self, user):
                self.from_user = user
                self.data = "show_stats"
            
            async def answer(self):
                pass
        
        update.callback_query = FakeQuery(update.effective_user)
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
        print("❌ Создайте config.py с токеном от @BotFather")
        print("Пример config.py:")
        print('TOKEN = "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"')
        return
    
    app = Application.builder().token(TOKEN).build()
    
    # Регистрация команд
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("quiz", quiz_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("help", show_help))
    
    # Обработчик кнопок
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("=" * 60)
    print("🤖 C1 ENGLISH BOT - ИСПРАВЛЕННАЯ ВЕРСИЯ")
    print("=" * 60)
    print("📚 База: 20+ слов уровня C1")
    print("🚀 Функции:")
    print("   • Кнопка '🚀 START QUIZ'")
    print("   • Бесконечный квиз (5 → новые 5 слов)")
    print("   • Исправлена ошибка 'Back to Menu'")
    print("   • Статистика обучения")
    print("=" * 60)
    print("🤖 Бот запущен! Найди в Telegram → /start")
    print("=" * 60)
    
    app.run_polling()

if __name__ == "__main__":
    main()
