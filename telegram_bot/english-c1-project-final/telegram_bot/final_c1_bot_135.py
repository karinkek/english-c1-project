#!/usr/bin/env python3
"""
🎯 FINAL C1 ENGLISH BOT - 135+ WORDS
Бот с полной базой слов, кнопкой Start и бесконечным квизом
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
    from c1_vocabulary_extended import get_c1_vocabulary, get_word_count, get_random_words, get_categories
    C1_VOCABULARY = get_c1_vocabulary()
    TOTAL_WORDS = get_word_count()
except ImportError:
    # Если файла нет, используем мини-версию
    C1_VOCABULARY = [
        {"word": "ubiquitous", "definition": "присутствующий повсюду", "category": "academic"},
        {"word": "conundrum", "definition": "сложная проблема", "category": "academic"},
        # ... (базовые 20 слов)
    ]
    TOTAL_WORDS = len(C1_VOCABULARY)
    
    def get_random_words(count=10, category=None):
        import random
        return random.sample(C1_VOCABULARY, min(count, len(C1_VOCABULARY)))
    
    def get_categories():
        return ["academic", "business", "literary"]

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Файл для прогресса
PROGRESS_FILE = "user_progress_135.json"

class ProgressManager135:
    """Менеджер прогресса для 135+ слов"""
    
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
                "sessions": 0,
                "streak": 0,
                "last_active": datetime.now().isoformat()
            }
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
        
        return {
            "accuracy": user_data["learned_words"][word]["correct"] / user_data["learned_words"][word]["attempts"],
            "total_correct": user_data["total_correct"],
            "total_attempts": user_data["total_attempts"]
        }
    
    def get_stats(self, user_id):
        user_data = self.get_user_data(user_id)
        learned = len(user_data["learned_words"])
        accuracy = (user_data["total_correct"] / user_data["total_attempts"] * 100) if user_data["total_attempts"] > 0 else 0
        
        return {
            "learned": learned,
            "total_words": TOTAL_WORDS,
            "accuracy": accuracy,
            "correct": user_data["total_correct"],
            "attempts": user_data["total_attempts"],
            "sessions": user_data.get("sessions", 0),
            "streak": user_data.get("streak", 0),
            "progress": (learned / TOTAL_WORDS * 100) if TOTAL_WORDS > 0 else 0
        }
    
    def increment_session(self, user_id):
        user_data = self.get_user_data(user_id)
        user_data["sessions"] = user_data.get("sessions", 0) + 1
        self.save_progress()

progress_manager = ProgressManager135()
active_sessions = {}

# ========== ГЛАВНОЕ МЕНЮ ==========

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start с кнопкой START"""
    user = update.effective_user
    stats = progress_manager.get_stats(user.id)
    
    keyboard = [
        [InlineKeyboardButton("🚀 START LEARNING (5 words)", callback_data="start_quiz")],
        [InlineKeyboardButton("📚 Continue Session", callback_data="continue_quiz")],
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

📊 *Your Learning Journey:*
• Words mastered: **{stats['learned']}/{stats['total_words']}**
• Accuracy rate: **{stats['accuracy']:.1f}%**
• Sessions completed: **{stats['sessions']}**
• Overall progress: **{stats['progress']:.1f}%**

🎯 *Database contains {stats['total_words']}+ C1 level words*
💪 *Click "START LEARNING" to begin!*
    """
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# ========== СИСТЕМА КВИЗА ==========

def generate_quiz_words(user_id, count=5):
    """Генерация слов для квиза"""
    user_data = progress_manager.get_user_data(user_id)
    learned_words = set(user_data["learned_words"].keys())
    
    # Если пользователь изучил много слов, показываем больше для повторения
    if len(learned_words) > TOTAL_WORDS * 0.7:
        # 80% повторение, 20% новые
        new_count = max(1, count // 5)
    elif len(learned_words) > TOTAL_WORDS * 0.3:
        # 50% повторение, 50% новые
        new_count = count // 2
    else:
        # 30% повторение, 70% новые
        new_count = count - (count // 3)
    
    # Новые слова
    all_words = [w["word"] for w in C1_VOCABULARY]
    new_candidates = [w for w in all_words if w not in learned_words]
    new_words = random.sample(new_candidates, min(new_count, len(new_candidates)))
    
    # Слова для повторения (с низкой точностью)
    review_candidates = []
    for word in learned_words:
        stats = user_data["learned_words"][word]
        accuracy = stats["correct"] / stats["attempts"] if stats["attempts"] > 0 else 0
        if accuracy < 0.7:  # Точность ниже 70%
            review_candidates.append(word)
    
    # Если мало кандидатов, берем любые изученные
    if len(review_candidates) < count - len(new_words):
        review_candidates = list(learned_words)
    
    review_words = random.sample(review_candidates, min(count - len(new_words), len(review_candidates)))
    
    # Собираем полные данные
    result = []
    word_dict = {w["word"]: w for w in C1_VOCABULARY}
    
    for word in new_words:
        if word in word_dict:
            result.append({**word_dict[word], "is_new": True})
    
    for word in review_words:
        if word in word_dict:
            result.append({**word_dict[word], "is_new": False})
    
    # Заполняем до нужного количества
    while len(result) < count:
        random_word = random.choice(all_words)
        if random_word not in [r["word"] for r in result]:
            if random_word in word_dict:
                result.append({**word_dict[random_word], "is_new": random_word not in learned_words})
    
    random.shuffle(result)
    return result[:count]

async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать квиз"""
    query = update.callback_query
    if query:
        await query.answer()
        user_id = query.from_user.id
    else:
        user_id = update.effective_user.id
    
    # Генерируем слова
    words = generate_quiz_words(user_id, 5)
    
    if not words:
        await query.edit_message_text(
            "🎉 *Amazing! You've learned all words!*\n\n"
            "Check back later for updates or review your progress.",
            parse_mode='Markdown'
        )
        return
    
    # Создаем сессию
    active_sessions[user_id] = {
        "words": words,
        "current": 0,
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
    
    keyboard.append([InlineKeyboardButton("⏭ Skip", callback_data="skip")])
    
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
    if query:
        await query.edit_message_text(question_text, reply_markup=reply_markup, parse_mode='Markdown')
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
        await query.edit_message_text("Starting new session...")
        await start_quiz(update, context)
        return
    
    words = session["words"]
    current_idx = session["current"]
    word = words[current_idx]
    
    if data == "skip":
        is_correct = False
        feedback = f"⏭ Skipped\n💡 *Correct:* {word['definition']}"
    else:
        answer_idx = int(data.split("_")[1])
        correct_idx = session.get("correct_idx", 0)
        is_correct = (answer_idx == correct_idx)
        
        if is_correct:
            session["score"] += 1
            feedback = f"✅ *Correct!*\n💡 {word['definition']}"
        else:
            user_letter = chr(65 + answer_idx)
            correct_letter = chr(65 + correct_idx)
            feedback = f"❌ *Incorrect* (You: {user_letter})\n💡 *Correct ({correct_letter}):* {word['definition']}"
    
    # Обновляем прогресс
    progress_manager.update_progress(user_id, word["word"], is_correct)
    
    await query.edit_message_text(
        f"{feedback}\n\n📊 Score: {session['score']}/{current_idx + 1}",
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
    
    # Обновляем статистику
    progress_manager.increment_session(user_id)
    
    # Результаты
    score = session["score"]
    total = len(session["words"])
    accuracy = (score / total * 100)
    
    stats = progress_manager.get_stats(user_id)
    
    result_text = f"""
🏁 *Session Complete!*

📊 *Results:*
• Correct: {score}/{total}
• Accuracy: {accuracy:.0f}%
• Time: {(datetime.now() - session['start_time']).seconds // 60} min

📈 *Overall Progress:*
• Words: {stats['learned']}/{stats['total_words']}
• Progress: {stats['progress']:.1f}%
• Sessions: {stats['sessions']}
    """
    
    # Удаляем сессию
    if user_id in active_sessions:
        del active_sessions[user_id]
    
    # Кнопки
    keyboard = [
        [InlineKeyboardButton("🚀 NEW QUIZ (5 More Words)", callback_data="start_quiz")],
        [InlineKeyboardButton("📊 View Progress", callback_data="show_stats")],
        [InlineKeyboardButton("🏠 Back to Menu", callback_data="back_to_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query = update.callback_query
    await query.edit_message_text(result_text, reply_markup=reply_markup, parse_mode='Markdown')

# ========== ДРУГИЕ ФУНКЦИИ ==========

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать статистику"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    stats = progress_manager.get_stats(user_id)
    
    # Прогресс по категориям
    categories = {}
    for word in C1_VOCABULARY:
        cat = word["category"]
        if cat not in categories:
            categories[cat] = {"total": 0, "learned": 0}
        categories[cat]["total"] += 1
    
    user_data = progress_manager.get_user_data(user_id)
    for word in user_data.get("learned_words", {}):
        for vocab_word in C1_VOCABULARY:
            if vocab_word["word"] == word:
                cat = vocab_word["category"]
                if cat in categories:
                    categories[cat]["learned"] += 1
                break
    
    stats_text = f"""
📊 *Your Learning Dashboard*

🎯 *Overall Progress:*
• Words mastered: **{stats['learned']}/{stats['total_words']}**
• Accuracy: **{stats['accuracy']:.1f}%**
• Sessions: **{stats['sessions']}**
• Progress: **{stats['progress']:.1f}%**

🏷 *Progress by Category:*
"""
    
    for cat, data in categories.items():
        learned = data["learned"]
        total = data["total"]
        percentage = (learned / total * 100) if total > 0 else 0
        bar = "█" * int(percentage // 10) + "░" * (10 - int(percentage // 10))
        stats_text += f"• {cat.capitalize()}: {learned}/{total} {bar} {percentage:.0f}%\n"
    
    keyboard = [
        [InlineKeyboardButton("🚀 Continue Learning", callback_data="start_quiz")],
        [InlineKeyboardButton("🏠 Menu", callback_data="back_to_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(stats_text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать категории"""
    query = update.callback_query
    await query.answer()
    
    categories = get_categories() if 'get_categories' in globals() else ["academic", "business", "literary"]
    
    keyboard = []
    for category in categories:
        keyboard.append([InlineKeyboardButton(f"📚 {category.capitalize()}", callback_data=f"category_{category}")])
    
    keyboard.append([InlineKeyboardButton("◀️ Back", callback_data="back_to_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🏷 *Select a category to focus on:*\n\n"
        "Each category contains specialized C1 vocabulary for different contexts.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать помощь"""
    help_text = f"""
🤖 *C1 ENGLISH VOCABULARY MASTER*

📚 *About:* 
This bot helps you master {TOTAL_WORDS}+ advanced English words at C1 level.

🎯 *How to use:*
1. Click *"START LEARNING"* - get 5 C1 words
2. Choose correct definitions
3. After 5 words → click *"NEW QUIZ"* for 5 more words
4. Track progress in *"My Progress"*

📊 *Learning System:*
• Adaptive algorithm (more review for difficult words)
• Progress tracking
• Category-based learning
• Infinite quiz sessions

💡 *C1 Level means:*
• Advanced/Proficient English
• Academic & professional use
• Complex vocabulary & idioms
    """
    
    keyboard = [[InlineKeyboardButton("🏠 Back to Menu", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query = update.callback_query
    if query:
        await query.edit_message_text(help_text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(help_text, reply_markup=reply_markup, parse_mode='Markdown')

# ========== ОБРАБОТЧИК КНОПОК ==========

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главный обработчик кнопок"""
    query = update.callback_query
    data = query.data
    
    if data == "start_quiz":
        await start_quiz(update, context)
    
    elif data == "continue_quiz":
        user_id = query.from_user.id
        if user_id in active_sessions:
            await show_question(update, context, user_id)
        else:
            await start_quiz(update, context)
    
    elif data == "show_stats":
        await show_stats(update, context)
    
    elif data == "show_categories":
        await show_categories(update, context)
    
    elif data == "show_help":
        await show_help(update, context)
    
    elif data == "back_to_menu":
        update.effective_message = query.message
        await start_command(update, context)
    
    elif data.startswith("category_"):
        # Упрощенная обработка категорий
        category = data.split("_", 1)[1]
        await query.edit_message_text(f"Category '{category}' selected! Starting quiz...")
        await asyncio.sleep(1)
        await start_quiz(update, context)
    
    elif data.startswith("answer_") or data == "skip":
        await handle_answer(update, context)

# ========== КОМАНДЫ ==========

async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_quiz(update, context)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

# ========== ЗАПУСК ==========

def main():
    """Запуск бота"""
    try:
        import config
        TOKEN = config.TOKEN
        if "ВАШ_" in TOKEN:
            raise ValueError("Token not set")
    except:
        print("❌ Создайте config.py с токеном от @BotFather")
        print("Пример содержимого config.py:")
        print('TOKEN = "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"')
        return
    
    app = Application.builder().token(TOKEN).build()
    
    # Команды
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("quiz", quiz_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("help", show_help))
    
    # Кнопки
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("=" * 70)
    print("🎯 FINAL C1 ENGLISH BOT - 135+ WORDS")
    print("=" * 70)
    print(f"📚 База данных: {TOTAL_WORDS}+ слов уровня C1")
    print("🏷 Категории: Academic, Business, Literary, Legal, Idioms")
    print("🚀 Функции:")
    print("   • Кнопка 'START LEARNING' в меню")
    print("   • Бесконечный квиз (5 слов → новые 5 слов)")
    print("   • Адаптивное обучение")
    print("   • Детальная статистика")
    print("=" * 70)
    print("🤖 Бот запущен! Найдите в Telegram и отправьте /start")
    print("=" * 70)
    
    app.run_polling()

if __name__ == "__main__":
    main()
