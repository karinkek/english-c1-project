#!/usr/bin/env python3
"""
🎯 FINAL C1 ENGLISH BOT - 150+ WORDS
Полная версия бота с исправленной навигацией
"""

import logging
import random
import asyncio
import json
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Импортируем полную базу слов
try:
    from full_c1_vocabulary import C1_VOCABULARY, get_word_count, get_random_words, get_categories
    TOTAL_WORDS = get_word_count()
except ImportError:
    # Если файла нет, создаем минимальную версию
    print("⚠️  full_c1_vocabulary.py не найден, используем минимальную базу")
    C1_VOCABULARY = [
        {"word": "ubiquitous", "definition": "присутствующий повсюду", "category": "academic"},
        {"word": "conundrum", "definition": "сложная проблема", "category": "academic"},
        # ... (остальные слова из fixed_c1_bot.py)
    ]
    TOTAL_WORDS = len(C1_VOCABULARY)
    
    def get_random_words(count=10, category=None):
        import random
        return random.sample(C1_VOCABULARY, min(count, len(C1_VOCABULARY)))
    
    def get_categories():
        categories = set(word["category"] for word in C1_VOCABULARY)
        return list(categories)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Файл для прогресса
PROGRESS_FILE = "user_progress.json"

class ProgressManager:
    """Менеджер прогресса"""
    
    def __init__(self):
        self.data = self.load_progress()
    
    def load_progress(self):
        if os.path.exists(PROGRESS_FILE):
            try:
                with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_progress(self):
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def get_user_data(self, user_id):
        if str(user_id) not in self.data:
            self.data[str(user_id)] = {
                "learned_words": {},
                "total_correct": 0,
                "total_attempts": 0,
                "sessions_completed": 0,
                "daily_streak": 0,
                "last_active": datetime.now().isoformat()
            }
            self.save_progress()
        return self.data[str(user_id)]
    
    def update_progress(self, user_id, word, is_correct):
        user_data = self.get_user_data(user_id)
        
        if word not in user_data["learned_words"]:
            user_data["learned_words"][word] = {"correct": 0, "attempts": 0}
        
        user_data["learned_words"][word]["attempts"] += 1
        user_data["total_attempts"] += 1
        
        if is_correct:
            user_data["learned_words"][word]["correct"] += 1
            user_data["total_correct"] += 1
        
        user_data["last_active"] = datetime.now().isoformat()
        self.save_progress()
        
        return user_data["learned_words"][word]
    
    def get_stats(self, user_id):
        user_data = self.get_user_data(user_id)
        learned_count = len(user_data["learned_words"])
        accuracy = (user_data["total_correct"] / user_data["total_attempts"] * 100) if user_data["total_attempts"] > 0 else 0
        
        return {
            "learned_words": learned_count,
            "total_words": TOTAL_WORDS,
            "accuracy": accuracy,
            "total_correct": user_data["total_correct"],
            "total_attempts": user_data["total_attempts"],
            "sessions": user_data.get("sessions_completed", 0),
            "streak": user_data.get("daily_streak", 0),
            "progress_percent": (learned_count / TOTAL_WORDS * 100) if TOTAL_WORDS > 0 else 0
        }
    
    def increment_session(self, user_id):
        user_data = self.get_user_data(user_id)
        user_data["sessions_completed"] = user_data.get("sessions_completed", 0) + 1
        self.save_progress()

progress_manager = ProgressManager()
active_sessions = {}

# ========== ГЛАВНОЕ МЕНЮ ==========

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start - главное меню"""
    user = update.effective_user
    stats = progress_manager.get_stats(user.id)
    
    # Создаем клавиатуру
    keyboard = [
        [InlineKeyboardButton("🚀 START QUIZ (5 words)", callback_data="start_quiz")],
        [
            InlineKeyboardButton("📊 My Progress", callback_data="show_stats"),
            InlineKeyboardButton("🏷 Categories", callback_data="show_categories")
        ],
        [InlineKeyboardButton("💡 How it works", callback_data="show_help")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = f"""
🎓 *C1 ENGLISH VOCABULARY MASTER*

*Welcome, {user.first_name}!*

📚 *Database: {stats['total_words']}+ C1 level words*
📈 *Your progress: {stats['progress_percent']:.1f}%*

📊 *Your Stats:*
• Words learned: **{stats['learned_words']}/{stats['total_words']}**
• Accuracy: **{stats['accuracy']:.1f}%**
• Sessions: **{stats['sessions']}**
• Streak: **{stats['streak']} days**

🎯 *Click START QUIZ to begin learning!*
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

def generate_quiz(user_id, count=5):
    """Генерация квиза с адаптивным подбором слов"""
    user_data = progress_manager.get_user_data(user_id)
    learned_words = set(user_data["learned_words"].keys())
    
    # Все доступные слова
    all_words = [w["word"] for w in C1_VOCABULARY]
    
    # Новые слова (еще не изученные)
    new_words = [w for w in all_words if w not in learned_words]
    
    # Слова для повторения (изученные с низкой точностью)
    review_words = []
    for word in learned_words:
        if word in user_data["learned_words"]:
            stats = user_data["learned_words"][word]
            accuracy = stats["correct"] / stats["attempts"] if stats["attempts"] > 0 else 0
            if accuracy < 0.7:  # Точность ниже 70%
                review_words.append(word)
    
    # Если мало слов для повторения, берем любые изученные
    if len(review_words) < 2:
        review_words = list(learned_words)[:3]
    
    # Баланс: 60% новых, 40% для повторения
    new_count = min(count * 6 // 10, len(new_words))
    review_count = min(count - new_count, len(review_words))
    
    # Если новых слов мало, добавляем больше для повторения
    if new_count == 0:
        review_count = min(count, len(review_words))
    
    # Выбираем слова
    selected_words = []
    word_dict = {w["word"]: w for w in C1_VOCABULARY}
    
    # Новые слова
    if new_words and new_count > 0:
        selected_new = random.sample(new_words, new_count)
        for word in selected_new:
            if word in word_dict:
                selected_words.append({**word_dict[word], "is_new": True})
    
    # Слова для повторения
    if review_words and review_count > 0:
        selected_review = random.sample(review_words, review_count)
        for word in selected_review:
            if word in word_dict:
                selected_words.append({**word_dict[word], "is_new": False})
    
    # Если все еще мало слов, добавляем случайные
    while len(selected_words) < count and all_words:
        random_word = random.choice(all_words)
        if random_word not in [w["word"] for w in selected_words]:
            if random_word in word_dict:
                is_new = random_word not in learned_words
                selected_words.append({**word_dict[random_word], "is_new": is_new})
    
    random.shuffle(selected_words)
    return selected_words[:count]

async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать квиз"""
    query = update.callback_query
    if query:
        await query.answer()
        user_id = query.from_user.id
    else:
        user_id = update.effective_user.id
    
    # Генерируем слова для квиза
    words = generate_quiz(user_id, 5)
    
    if not words:
        if query:
            await query.edit_message_text(
                "🎉 *Congratulations!*\n\nYou've learned all available words!\n\n"
                "Check back later for updates or review your progress.",
                parse_mode='Markdown'
            )
        return
    
    # Создаем сессию
    active_sessions[user_id] = {
        "words": words,
        "current_index": 0,
        "score": 0,
        "start_time": datetime.now()
    }
    
    await show_question(update, context, user_id)

async def show_question(update, context, user_id):
    """Показать вопрос"""
    session = active_sessions.get(user_id)
    if not session:
        await start_quiz(update, context)
        return
    
    words = session["words"]
    current_idx = session["current_index"]
    
    if current_idx >= len(words):
        await finish_quiz(update, context, user_id)
        return
    
    word = words[current_idx]
    
    # Создаем варианты ответов
    correct_def = word["definition"]
    
    # Собираем другие определения
    all_defs = [w["definition"] for w in C1_VOCABULARY if w["definition"] != correct_def]
    wrong_defs = random.sample(all_defs, min(3, len(all_defs)))
    
    options = wrong_defs + [correct_def]
    random.shuffle(options)
    correct_idx = options.index(correct_def)
    
    # Сохраняем правильный ответ
    session["correct_idx"] = correct_idx
    active_sessions[user_id] = session
    
    # Создаем кнопки
    keyboard = []
    for i, option in enumerate(options):
        keyboard.append([InlineKeyboardButton(f"{chr(65+i)}. {option}", callback_data=f"answer_{i}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Текст вопроса
    question_num = current_idx + 1
    question_text = f"""
{'🆕' if word.get('is_new') else '🔄'} *Question {question_num}/5*

📖 *Word:* `{word['word']}`
🏷 *Category:* {word['category'].capitalize()}

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
    current_idx = session["current_index"]
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
    progress_manager.update_progress(user_id, word["word"], is_correct)
    
    # Показываем результат
    await query.edit_message_text(
        f"{feedback}\n\n💡 *Definition:* {word['definition']}\n\n"
        f"📊 *Score:* {session['score']}/{current_idx + 1}",
        parse_mode='Markdown'
    )
    
    # Переходим к следующему вопросу
    session["current_index"] += 1
    active_sessions[user_id] = session
    
    await asyncio.sleep(2)
    
    if session["current_index"] < len(words):
        await show_question(update, context, user_id)
    else:
        await finish_quiz(update, context, user_id)

async def finish_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id):
    """Завершение квиза"""
    session = active_sessions.get(user_id)
    if not session:
        return
    
    # Обновляем статистику сессий
    progress_manager.increment_session(user_id)
    
    # Вычисляем результаты
    score = session["score"]
    total = len(session["words"])
    accuracy = (score / total * 100) if total > 0 else 0
    
    # Получаем общую статистику
    stats = progress_manager.get_stats(user_id)
    
    result_text = f"""
🏁 *Quiz Complete!*

📊 *Session Results:*
• Correct: {score}/{total}
• Accuracy: {accuracy:.0f}%
• Time: {(datetime.now() - session['start_time']).seconds // 60} min

📈 *Overall Progress:*
• Words: {stats['learned_words']}/{stats['total_words']}
• Progress: {stats['progress_percent']:.1f}%
• Sessions: {stats['sessions']}
"""
    
    # Удаляем сессию
    if user_id in active_sessions:
        del active_sessions[user_id]
    
    # Кнопки для продолжения
    keyboard = [
        [InlineKeyboardButton("🚀 NEW QUIZ (5 More Words)", callback_data="start_quiz")],
        [InlineKeyboardButton("📊 View Progress", callback_data="show_stats")],
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
    stats = progress_manager.get_stats(user_id)
    
    # Подсчитываем прогресс по категориям
    categories = {}
    for word in C1_VOCABULARY:
        cat = word["category"]
        if cat not in categories:
            categories[cat] = {"total": 0, "learned": 0}
        categories[cat]["total"] += 1
    
    user_data = progress_manager.get_user_data(user_id)
    for learned_word in user_data.get("learned_words", {}):
        # Находим категорию слова
        for vocab_word in C1_VOCABULARY:
            if vocab_word["word"] == learned_word:
                cat = vocab_word["category"]
                if cat in categories:
                    categories[cat]["learned"] += 1
                break
    
    stats_text = f"""
📊 *Your Learning Dashboard*
🤖 *How to Use C1 Vocabulary Bot*

🎯 *Learning System:*
• The bot uses *spaced repetition* to optimize memory retention
• Each quiz contains a mix of *new words* and *review words*
• Your progress is tracked and saved automatically

📚 *Categories:*
1. *Academic* - Advanced academic vocabulary
2. *Business* - Professional business terms
3. *Literary* - Literary and expressive words
4. *Legal* - Formal and legal terminology

🎮 *Quiz Format:*
• Each quiz has 5 questions
• For each word, choose the correct definition
• Immediate feedback after each answer
• Progress tracking with accuracy statistics

📊 *Progress Tracking:*
• Words learned: How many unique words you've practiced
• Accuracy: Your overall correct answer rate
• Sessions: Number of completed quizzes
• Streak: Consecutive days of practice

💡 *Tips:*
• Practice regularly for best results
• Review difficult words more frequently
• Use context clues for unfamiliar words
"""
    
    keyboard = [
        [InlineKeyboardButton("🚀 Start Learning", callback_data="start_quiz")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        help_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def daily_challenge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ежедневное испытание"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # Выбираем 10 слов для ежедневного испытания
    words = get_random_words(10)
    
    active_sessions[user_id] = {
        "words": words,
        "current_index": 0,
        "score": 0,
        "start_time": datetime.now(),
        "is_daily": True
    }
    
    await query.edit_message_text(
        "🔥 *Daily Challenge Started!*\n\n"
        "Complete 10 questions to maintain your streak!\n\n"
        "Good luck! 🍀",
        parse_mode='Markdown'
    )
    
    await asyncio.sleep(2)
    await show_question(update, context, user_id)

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вернуться в главное меню"""
    await start_command(update, context)

async def view_all_words(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать все слова"""
    query = update.callback_query
    await query.answer()
    
    # Разбиваем на страницы
    page_size = 20
    page = int(context.args[0]) if context.args else 0
    
    start_idx = page * page_size
    end_idx = start_idx + page_size
    
    words_text = ""
    for i, word in enumerate(C1_VOCABULARY[start_idx:end_idx], start=1):
        words_text += f"• `{word['word']}` - {word['definition']} ({word['category']})\n"
    
    total_pages = (len(C1_VOCABULARY) + page_size - 1) // page_size
    
    keyboard = []
    if page > 0:
        keyboard.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"page_{page-1}"))
    if page < total_pages - 1:
        keyboard.append(InlineKeyboardButton("Next ➡️", callback_data=f"page_{page+1}"))
    
    keyboard.append(InlineKeyboardButton("🏠 Menu", callback_data="back_to_menu"))
    
    reply_markup = InlineKeyboardMarkup([keyboard]) if keyboard else None
    
    await query.edit_message_text(
        f"📚 *Complete Word List ({start_idx+1}-{min(end_idx, len(C1_VOCABULARY))}/{len(C1_VOCABULARY)})*\n\n"
        f"{words_text}",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# ========== ОСНОВНАЯ ФУНКЦИЯ ==========

def main():
    """Запуск бота"""
    # Чтение токена из переменной окружения или файла
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not TOKEN:
        try:
            with open("bot_token.txt", "r") as f:
                TOKEN = f.read().strip()
        except:
            print("❌ Ошибка: Токен не найден!")
            print("Создайте файл 'bot_token.txt' с токеном или установите переменную окружения TELEGRAM_BOT_TOKEN")
            return
    
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()
    
    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("stats", show_stats))
    application.add_handler(CommandHandler("help", show_help))
    application.add_handler(CommandHandler("words", view_all_words))
    
    # Регистрируем обработчики callback
    application.add_handler(CallbackQueryHandler(start_quiz, pattern="^start_quiz$"))
    application.add_handler(CallbackQueryHandler(show_stats, pattern="^show_stats$"))
    application.add_handler(CallbackQueryHandler(show_categories, pattern="^show_categories$"))
    application.add_handler(CallbackQueryHandler(show_help, pattern="^show_help$"))
    application.add_handler(CallbackQueryHandler(back_to_menu, pattern="^back_to_menu$"))
    application.add_handler(CallbackQueryHandler(practice_category, pattern="^practice_"))
    application.add_handler(CallbackQueryHandler(daily_challenge, pattern="^daily_challenge$"))
    application.add_handler(CallbackQueryHandler(handle_answer, pattern="^answer_"))
    application.add_handler(CallbackQueryHandler(view_all_words, pattern="^page_"))
    
    # Запускаем бота
    print("🤖 C1 Vocabulary Bot запущен!")
    print(f"📊 База данных: {TOTAL_WORDS} слов")
    print("👥 Ожидание сообщений...")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
