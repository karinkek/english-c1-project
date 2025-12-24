#!/usr/bin/env python3
"""
🤖 C1 Vocabulary Telegram Bot
Бот для изучения английских слов уровня C1
"""
import logging
import random
import asyncio
import json
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ========== БАЗА ДАННЫХ СЛОВ ==========

C1_VOCABULARY = [
    # ========== ACADEMIC (50 слов) ==========
    {"word": "ubiquitous", "definition": "присутствующий повсюду", "category": "academic"},
    {"word": "conundrum", "definition": "сложная проблема", "category": "academic"},
    {"word": "ephemeral", "definition": "кратковременный", "category": "academic"},
    {"word": "perfunctory", "definition": "поверхностный, формальный", "category": "academic"},
    {"word": "equivocate", "definition": "уклоняться от ответа", "category": "academic"},
    {"word": "laconic", "definition": "краткий, немногословный", "category": "academic"},
    {"word": "prolific", "definition": "плодовитый, продуктивный", "category": "academic"},
    {"word": "quintessential", "definition": "наиболее типичный", "category": "academic"},
    {"word": "voracious", "definition": "ненасытный, жадный", "category": "academic"},
    {"word": "dichotomy", "definition": "разделение на две части", "category": "academic"},
    {"word": "paradigm", "definition": "модель, образец", "category": "academic"},
    {"word": "ambiguous", "definition": "имеющий несколько значений", "category": "academic"},
    {"word": "comprehensive", "definition": "всеобъемлющий", "category": "academic"},
    {"word": "convoluted", "definition": "запутанный, сложный", "category": "academic"},
    {"word": "scrutinize", "definition": "тщательно изучать", "category": "academic"},
    {"word": "meticulous", "definition": "очень внимательный к деталям", "category": "academic"},
    {"word": "didactic", "definition": "поучительный, назидательный", "category": "academic"},
    {"word": "esoteric", "definition": "понятный только посвященным", "category": "academic"},
    {"word": "heuristic", "definition": "помогающий открывать новое", "category": "academic"},
    {"word": "idiosyncratic", "definition": "своеобразный, индивидуальный", "category": "academic"},
    {"word": "juxtaposition", "definition": "сопоставление", "category": "academic"},
    {"word": "myriad", "definition": "бесчисленное множество", "category": "academic"},
    {"word": "ostensible", "definition": "внешний, кажущийся", "category": "academic"},
    {"word": "paradoxical", "definition": "парадоксальный", "category": "academic"},
    {"word": "rhetorical", "definition": "риторический", "category": "academic"},
    {"word": "sycophant", "definition": "подхалим, льстец", "category": "academic"},
    {"word": "taciturn", "definition": "молчаливый", "category": "academic"},
    {"word": "ubiquity", "definition": "вездесущность", "category": "academic"},
    {"word": "vicarious", "definition": "испытываемый через других", "category": "academic"},
    {"word": "wistful", "definition": "грустно-задумчивый", "category": "academic"},
    {"word": "abstruse", "definition": "трудный для понимания", "category": "academic"},
    {"word": "cacophony", "definition": "неприятный звук", "category": "academic"},
    {"word": "delineate", "definition": "очерчивать, описывать", "category": "academic"},
    {"word": "epistemology", "definition": "теория познания", "category": "academic"},
    {"word": "fallacious", "definition": "ошибочный, ложный", "category": "academic"},
    {"word": "gregarious", "definition": "общительный", "category": "academic"},
    {"word": "histrionic", "definition": "театральный, наигранный", "category": "academic"},
    {"word": "iconoclast", "definition": "ниспровергатель традиций", "category": "academic"},
    {"word": "jargon", "definition": "профессиональный жаргон", "category": "academic"},
    {"word": "kowtow", "definition": "униженно кланяться", "category": "academic"},
    {"word": "lucid", "definition": "ясный, понятный", "category": "academic"},
    {"word": "magnanimous", "definition": "великодушный", "category": "academic"},
    {"word": "nefarious", "definition": "злостный, преступный", "category": "academic"},
    {"word": "obfuscate", "definition": "запутывать, затемнять", "category": "academic"},
    {"word": "pedantic", "definition": "педантичный", "category": "academic"},
    {"word": "quandary", "definition": "затруднительное положение", "category": "academic"},
    {"word": "recalcitrant", "definition": "упрямый, непокорный", "category": "academic"},
    {"word": "sagacious", "definition": "мудрый, проницательный", "category": "academic"},
    {"word": "truculent", "definition": "агрессивный, воинственный", "category": "academic"},
    
    # ========== BUSINESS (35 слов) ==========
    {"word": "leverage", "definition": "использовать эффективно", "category": "business"},
    {"word": "synergy", "definition": "взаимодействие с усилением", "category": "business"},
    {"word": "streamline", "definition": "оптимизировать", "category": "business"},
    {"word": "benchmark", "definition": "эталон, стандарт", "category": "business"},
    {"word": "proactive", "definition": "активный, инициативный", "category": "business"},
    {"word": "viable", "definition": "жизнеспособный", "category": "business"},
    {"word": "contingency", "definition": "план на случай проблем", "category": "business"},
    {"word": "disseminate", "definition": "распространять", "category": "business"},
    {"word": "facilitate", "definition": "способствовать", "category": "business"},
    {"word": "incentivize", "definition": "стимулировать", "category": "business"},
    {"word": "mitigate", "definition": "смягчать, уменьшать", "category": "business"},
    {"word": "nuance", "definition": "тонкое различие", "category": "business"},
    {"word": "pragmatic", "definition": "практичный", "category": "business"},
    {"word": "robust", "definition": "прочный, надежный", "category": "business"},
    {"word": "scalable", "definition": "масштабируемый", "category": "business"},
    {"word": "transparent", "definition": "прозрачный", "category": "business"},
    {"word": "validate", "definition": "подтверждать", "category": "business"},
    {"word": "wholesale", "definition": "оптовый", "category": "business"},
    {"word": "yield", "definition": "приносить результат", "category": "business"},
    {"word": "acumen", "definition": "проницательность", "category": "business"},
    {"word": "bottleneck", "definition": "узкое место", "category": "business"},
    {"word": "consensus", "definition": "общее согласие", "category": "business"},
    {"word": "diligent", "definition": "усердный", "category": "business"},
    {"word": "expedite", "definition": "ускорять", "category": "business"},
    {"word": "feasibility", "definition": "осуществимость", "category": "business"},
    {"word": "gauge", "definition": "оценивать, измерять", "category": "business"},
    {"word": "holistic", "definition": "целостный", "category": "business"},
    {"word": "increment", "definition": "приращение", "category": "business"},
    {"word": "juxtapose", "definition": "сопоставлять", "category": "business"},
    {"word": "kudos", "definition": "похвала, признание", "category": "business"},
    {"word": "liaise", "definition": "поддерживать связь", "category": "business"},
    {"word": "milestone", "definition": "важный этап", "category": "business"},
    {"word": "nexus", "definition": "связь, соединение", "category": "business"},
    {"word": "outlay", "definition": "затраты, расходы", "category": "business"},
    {"word": "paradigm shift", "definition": "смена парадигмы", "category": "business"},
    
    # ========== LITERARY (40 слов) ==========
    {"word": "serendipity", "definition": "счастливая случайность", "category": "literary"},
    {"word": "melancholy", "definition": "грусть, меланхолия", "category": "literary"},
    {"word": "epiphany", "definition": "озарение", "category": "literary"},
    {"word": "nostalgia", "definition": "тоска по прошлому", "category": "literary"},
    {"word": "eloquent", "definition": "красноречивый", "category": "literary"},
    {"word": "arduous", "definition": "трудный, тяжелый", "category": "literary"},
    {"word": "ambivalent", "definition": "двойственный", "category": "literary"},
    {"word": "candid", "definition": "откровенный", "category": "literary"},
    {"word": "dubious", "definition": "сомнительный", "category": "literary"},
    {"word": "elusive", "definition": "ускользающий", "category": "literary"},
    {"word": "frivolous", "definition": "легкомысленный", "category": "literary"},
    {"word": "haphazard", "definition": "случайный", "category": "literary"},
    {"word": "incessant", "definition": "непрерывный", "category": "literary"},
    {"word": "jubilant", "definition": "ликующий", "category": "literary"},
    {"word": "kaleidoscopic", "definition": "постоянно меняющийся", "category": "literary"},
    {"word": "languid", "definition": "вялый, медлительный", "category": "literary"},
    {"word": "mellifluous", "definition": "мелодичный, сладкозвучный", "category": "literary"},
    {"word": "narcissistic", "definition": "самовлюбленный", "category": "literary"},
    {"word": "opulent", "definition": "богатый, роскошный", "category": "literary"},
    {"word": "placid", "definition": "спокойный, мирный", "category": "literary"},
    {"word": "quixotic", "definition": "рыцарский, непрактичный", "category": "literary"},
    {"word": "resilient", "definition": "устойчивый", "category": "literary"},
    {"word": "verbose", "definition": "многословный", "category": "literary"},
    {"word": "whimsical", "definition": "причудливый", "category": "literary"},
    {"word": "xenophobic", "definition": "ксенофобский", "category": "literary"},
    {"word": "yearning", "definition": "сильное желание", "category": "literary"},
    {"word": "zealous", "definition": "ревностный", "category": "literary"},
    {"word": "aesthetic", "definition": "эстетический", "category": "literary"},
    {"word": "bucolic", "definition": "пасторальный, сельский", "category": "literary"},
    {"word": "cathartic", "definition": "очищающий", "category": "literary"},
    {"word": "ethereal", "definition": "воздушный, неземной", "category": "literary"},
    {"word": "furtive", "definition": "скрытный, тайный", "category": "literary"},
    {"word": "garrulous", "definition": "болтливый", "category": "literary"},
    {"word": "haughty", "definition": "высокомерный", "category": "literary"},
    {"word": "idyllic", "definition": "идиллический", "category": "literary"},
    {"word": "lucid", "definition": "ясный, понятный", "category": "literary"},
    {"word": "magnanimous", "definition": "великодушный", "category": "literary"},
    {"word": "nefarious", "definition": "злостный, преступный", "category": "literary"},
    {"word": "obfuscate", "definition": "запутывать, затемнять", "category": "literary"},
    {"word": "pedantic", "definition": "педантичный", "category": "literary"},
    
    # ========== LEGAL & FORMAL (25 слов) ==========
    {"word": "jurisdiction", "definition": "юрисдикция", "category": "legal"},
    {"word": "litigation", "definition": "судебный процесс", "category": "legal"},
    {"word": "precedent", "definition": "прецедент", "category": "legal"},
    {"word": "mandatory", "definition": "обязательный", "category": "legal"},
    {"word": "compliance", "definition": "соблюдение", "category": "legal"},
    {"word": "arbitration", "definition": "арбитраж", "category": "legal"},
    {"word": "nullify", "definition": "аннулировать", "category": "legal"},
    {"word": "liability", "definition": "ответственность", "category": "legal"},
    {"word": "statute", "definition": "закон, устав", "category": "legal"},
    {"word": "testimony", "definition": "показания", "category": "legal"},
    {"word": "allegation", "definition": "утверждение, обвинение", "category": "legal"},
    {"word": "breach", "definition": "нарушение", "category": "legal"},
    {"word": "culpable", "definition": "виновный", "category": "legal"},
    {"word": "deterrent", "definition": "сдерживающий фактор", "category": "legal"},
    {"word": "entitlement", "definition": "право, привилегия", "category": "legal"},
    {"word": "grievance", "definition": "жалоба", "category": "legal"},
    {"word": "hierarchy", "definition": "иерархия", "category": "legal"},
    {"word": "impartial", "definition": "беспристрастный", "category": "legal"},
    {"word": "judicious", "definition": "благоразумный", "category": "legal"},
    {"word": "negligence", "definition": "небрежность", "category": "legal"},
    {"word": "omission", "definition": "упущение", "category": "legal"},
    {"word": "preclude", "definition": "исключать", "category": "legal"},
    {"word": "quash", "definition": "аннулировать", "category": "legal"},
    {"word": "ratify", "definition": "ратифицировать", "category": "legal"},
    {"word": "subpoena", "definition": "судебная повестка", "category": "legal"},
]

TOTAL_WORDS = len(C1_VOCABULARY)

def get_random_words(count=10, category=None):
    """Получить случайные слова"""
    if category:
        words = [w for w in C1_VOCABULARY if w["category"] == category]
    else:
        words = C1_VOCABULARY
    return random.sample(words, min(count, len(words)))

def get_categories():
    """Получить список категорий"""
    categories = set(word["category"] for word in C1_VOCABULARY)
    return list(categories)

# ========== НАСТРОЙКА ЛОГИРОВАНИЯ ==========

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== МЕНЕДЖЕР ПРОГРЕССА ==========

PROGRESS_FILE = "user_progress.json"

class ProgressManager:
    """Управление прогрессом пользователей"""
    
    def __init__(self):
        self.data = self.load_progress()
    
    def load_progress(self):
        """Загрузить прогресс из файла"""
        if os.path.exists(PROGRESS_FILE):
            try:
                with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_progress(self):
        """Сохранить прогресс в файл"""
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def get_user_data(self, user_id):
        """Получить данные пользователя"""
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
        """Обновить прогресс пользователя"""
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
        """Получить статистику пользователя"""
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
        """Увеличить счетчик сессий"""
        user_data = self.get_user_data(user_id)
        user_data["sessions_completed"] = user_data.get("sessions_completed", 0) + 1
        self.save_progress()

# Создаем менеджер прогресса
progress_manager = ProgressManager()

# Активные сессии пользователей
active_sessions = {}

# ========== КОМАНДЫ И ФУНКЦИИ БОТА ==========

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
    
    # Создаем текст статистики по категориям
    category_text = ""
    for cat_name, cat_data in categories.items():
        percent = (cat_data["learned"] / cat_data["total"] * 100) if cat_data["total"] > 0 else 0
        progress_bar = "█" * int(percent // 10) + "░" * (10 - int(percent // 10))
        category_text += f"\n📚 *{cat_name.capitalize()}:* {cat_data['learned']}/{cat_data['total']}\n{progress_bar} {percent:.1f}%"
    
    stats_text = f"""
📊 *Your Learning Dashboard*

🎯 *Overall Progress:*
• Words mastered: **{stats['learned_words']}/{stats['total_words']}**
• Accuracy: **{stats['accuracy']:.1f}%**
• Sessions completed: **{stats['sessions']}**
• Daily streak: **{stats['streak']} days**

📚 *Progress by Category:*{category_text}
    """
    
    # Создаем клавиатуру
    keyboard = [
        [InlineKeyboardButton("🚀 Practice More", callback_data="start_quiz")],
        [InlineKeyboardButton("🏷 Category Practice", callback_data="show_categories")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        stats_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать категории"""
    query = update.callback_query
    await query.answer()
    
    categories = get_categories()
    
    # Создаем кнопки для категорий
    keyboard = []
    for category in categories:
        # Подсчитываем слова в категории
        category_words = [w for w in C1_VOCABULARY if w["category"] == category]
        keyboard.append([
            InlineKeyboardButton(
                f"📚 {category.capitalize()} ({len(category_words)} words)",
                callback_data=f"practice_{category}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🏠 Back to Menu", callback_data="back_to_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📚 *Choose a category to practice:*\n\n"
        "Select a category to focus on specific vocabulary types.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def practice_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать практику по категории"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    category = data.split("_")[1]
    
    # Получаем слова категории
    category_words = [w for w in C1_VOCABULARY if w["category"] == category]
    
    if not category_words:
        await query.edit_message_text(f"No words found for category: {category}")
        return
    
    # Выбираем 5 случайных слов из категории
    words = random.sample(category_words, min(5, len(category_words)))
    
    user_id = query.from_user.id
    active_sessions[user_id] = {
        "words": words,
        "current_index": 0,
        "score": 0,
        "start_time": datetime.now(),
        "category": category
    }
    
    await show_question(update, context, user_id)

async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать справку"""
    query = update.callback_query
    await query.answer()
    
    help_text = """
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

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вернуться в главное меню"""
    await start_command(update, context)

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
    
    # Регистрируем обработчики callback
    application.add_handler(CallbackQueryHandler(start_quiz, pattern="^start_quiz$"))
    application.add_handler(CallbackQueryHandler(show_stats, pattern="^show_stats$"))
    application.add_handler(CallbackQueryHandler(show_categories, pattern="^show_categories$"))
    application.add_handler(CallbackQueryHandler(show_help, pattern="^show_help$"))
    application.add_handler(CallbackQueryHandler(back_to_menu, pattern="^back_to_menu$"))
    application.add_handler(CallbackQueryHandler(practice_category, pattern="^practice_"))
    application.add_handler(CallbackQueryHandler(handle_answer, pattern="^answer_"))
    
    # Запускаем бота
    print("🤖 C1 Vocabulary Bot запущен!")
    print(f"📊 База данных: {TOTAL_WORDS} слов")
    print("👥 Ожидание сообщений...")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
