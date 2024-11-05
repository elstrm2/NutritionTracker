import os
import logging
from sqlalchemy import delete
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
import redis.asyncio as redis
from dotenv import load_dotenv
from datetime import datetime, time
import pytz
from sqlalchemy.sql import func
import re
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from contextlib import asynccontextmanager

load_dotenv()

DEBUG_LEVEL = os.getenv("DEBUG_LEVEL").upper()

db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")

if db_password:
    DATABASE_URL = (
        f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    )
else:
    DATABASE_URL = f"postgresql+asyncpg://{db_user}@{db_host}:{db_port}/{db_name}"

logging.basicConfig(level=getattr(logging, DEBUG_LEVEL, logging.INFO))
logger = logging.getLogger(__name__)

pool_size = int(os.getenv("DB_POOL_SIZE"))
max_overflow = int(os.getenv("DB_MAX_OVERFLOW"))

engine = create_async_engine(
    DATABASE_URL,
    echo=(DEBUG_LEVEL == "DEBUG"),
    pool_size=pool_size,
    max_overflow=max_overflow,
)

async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

bot = Bot(token=os.getenv("TOKEN"))
dp = Dispatcher(bot)

if DEBUG_LEVEL == "DEBUG":
    from aiogram.contrib.middlewares.logging import LoggingMiddleware

    dp.middleware.setup(LoggingMiddleware())

redis_host = os.getenv("REDIS_HOST")
redis_port = int(os.getenv("REDIS_PORT"))
redis_password = os.getenv("REDIS_PASSWORD")
redis_db = int(os.getenv("REDIS_DB"))

if redis_password:
    redis_client = redis.Redis(
        host=redis_host,
        port=redis_port,
        password=redis_password,
        db=redis_db,
        decode_responses=True,
    )
else:
    redis_client = redis.Redis(
        host=redis_host,
        port=redis_port,
        db=redis_db,
        decode_responses=True,
    )

translations = {
    "en": {
        "start": "Hello! I will help you track calories and water. Enter your data with /set.",
        "data_updated": "Data updated successfully!",
        "enter_data_first": "Please enter your information first using /set.",
        "invalid_calories": "Invalid number of calories. Please enter a value between 10 and 100000.",
        "invalid_protein_fat_carbs": "Invalid amount of protein, fat, or carbs. Each should be between 0 and 100000.",
        "invalid_water": "Invalid amount of water. Please enter a value between 0.1 and 100 liters.",
        "calories_mismatch": "The total calories from protein, fat, and carbs do not match the provided calories.",
        "water_added": "You have added {water} liters of water.",
        "food_added": "You have added food with {calories} calories.",
        "invalid_timezone": "Invalid timezone format. Please use UTC±HH or UTC±HH:MM format. Examples: UTC+03, UTC-02, UTC+05:30.",
        "timezone_set": "Timezone set to {timezone}.",
        "invalid_language": "Invalid language. Only 'en' and 'ru' are available.",
        "language_changed": "Language changed to {language}.",
        "no_data_for_date": "No data for the specified date.",
        "invalid_comment": "The comment must be less than 100 characters.",
        "error_occurred": "An error occurred.",
        "set_info_usage": "Usage: /set <calories> <protein> <fat> <carbs> <water>. Example: /set 2000 150 50 250 2.5",
        "add_food_usage": (
            "Usage: /food <grams_eaten> <protein_per_100g> <fat_per_100g> <carbs_per_100g> [comment].\n"
            "Example: /food 150 10 5 20 Delicious porridge."
        ),
        "set_timezone_usage": "Usage: /time <timezone>. Examples: /time UTC+03, /time UTC-05:30",
        "set_language_usage": "Usage: /lang <en/ru>. Example: /lang ru",
        "add_water_usage": "Usage: /water <liters>. Example: /water 2.5",
        "get_daily_log_usage": "Usage: /log [date]. Example: /log 2023-10-15",
        "invalid_date_format": "Invalid date format. Please use YYYY-MM-DD.",
        "food_entry": "[{time}] Food: {calories} kcal, P: {protein}, F: {fat}, C: {carbohydrates}, Comment: {comment}",
        "water_entry": "[{time}] Water: {water} liters",
        "calculate_info_usage": (
            "Usage: /calc <age> <weight> <height> <metabolism> <activity> <goal> <desire> <diet_type> <gender> <body_fat> <climate> <rhr>.\n\n"
            "Parameters:\n"
            "- age: Integer between 1 and 200.\n"
            "- weight: Float between 1 and 1000 (kg).\n"
            "- height: Float between 1 and 1000 (cm).\n"
            "- metabolism: Integer between 1 and 10 or '-' (optional).\n"
            "- activity: Integer between 0 and 10 or '-' (optional).\n"
            "- goal: Integer -1 (lose weight), 0 (maintain weight), +1 (gain weight), or '-' (optional).\n"
            "- desire: Integer between 1 and 10 or '-' (how strongly you want to lose/gain weight). If '-', it won't be considered.\n"
            "- diet_type: Integer 0 (basic), 1 (protein), 2 (fat), 3 (carbohydrate), or '-' (optional).\n"
            "- gender: 'm' for male, 'f' for female, or '-' (optional).\n"
            "- body_fat: Float between 0.1 and 100 or '-' (optional).\n"
            "- climate: Integer -1 (cold), 0 (humid), 1 (hot), or '-' (optional).\n"
            "- rhr: Resting Heart Rate, integer between 40 and 140, or '-' (optional).\n\n"
            "Examples:\n"
            "/calc 30 70 175 5 5 -1 7 1 m 20 0 70\n"
            "/calc 25 60 160 - - - - 0 - - -"
        ),
        "invalid_age": "Invalid age. Please enter a value between 1 and 200.",
        "invalid_weight": "Invalid weight. Please enter a value between 1 and 1000.",
        "invalid_height": "Invalid height. Please enter a value between 1 and 1000.",
        "invalid_metabolism": "Invalid metabolism. Please enter a value between 1 and 10, or '-' if optional.",
        "invalid_activity": "Invalid activity. Please enter a value between 0 and 10, or '-' if optional.",
        "invalid_goal": "Invalid goal. Please enter -1 to lose weight, 0 to maintain, or +1 to gain weight, or '-' if optional.",
        "invalid_desire": "Invalid desire. Please enter a value between 1 and 10 or '-' if you do not want to change your weight.",
        "invalid_diet_type": "Invalid diet type. Please enter 0 for basic, 1 for protein, 2 for fat, or 3 for carbohydrate diet, or '-' if optional.",
        "invalid_gender": "Invalid gender. Please enter 'm' for male, 'f' for female, or '-' if optional.",
        "invalid_body_fat": "Invalid body fat percentage. Please enter a value between 0.1 and 100, or '-' if not applicable.",
        "invalid_climate": "Invalid climate value. Please enter -1 for cold, 0 for humid, or +1 for hot, or '-' if optional.",
        "invalid_rhr": "Invalid resting heart rate. Please enter a value between 40 and 140, or '-' if not applicable.",
        "auto_update_info": "Based on your information, please use the following command to update your data:\n{command}",
        "current_info_message": (
            "Current data:\n"
            "Calories: {calories} kcal\n"
            "Protein: {protein} g\n"
            "Fat: {fat} g\n"
            "Carbohydrates: {carbohydrates} g\n"
            "Water: {water} liters"
        ),
        "daily_progress_message": (
            "Daily progress for {date}:\n"
            "Eaten: {calories_eaten} out of {calories_total} kcal\n"
            "Remaining: {calories_remaining} kcal\n\n"
            "Protein: {protein_eaten} out of {protein_total} g (remaining: {protein_remaining} g)\n"
            "Fat: {fat_eaten} out of {fat_total} g (remaining: {fat_remaining} g)\n"
            "Carbohydrates: {carbs_eaten} out of {carbs_total} g (remaining: {carbs_remaining} g)\n\n"
            "Water: {water_drank} out of {water_total} liters (remaining: {water_remaining} liters)"
        ),
        "daily_food_and_water_log": "Detailed log of food and water intake for {date}:",
        "get_daily_progress_usage": "Usage: /progress [date]. Example: /progress 2023-10-15",
        "user_count_message": "The total number of users is {count}.",
        "invalid_grams_eaten": "Invalid grams eaten. Please enter a value between 1 and 100000 grams.",
        "invalid_macros": "Invalid values for protein, fat, or carbohydrates. Each should be between 0 and 100000.",
        "no_non_zero_macro": "At least one of protein, fat, or carbohydrates must be greater than zero.",
    },
    "ru": {
        "start": "Привет! Я помогу тебе отслеживать калории и воду. Введи свои данные через команду /set.",
        "data_updated": "Данные обновлены успешно!",
        "enter_data_first": "Пожалуйста, сначала введи свои данные через команду /set.",
        "invalid_calories": "Неверное количество калорий. Пожалуйста, введи значение от 10 до 100000.",
        "invalid_protein_fat_carbs": "Неверное количество белков, жиров или углеводов. Каждое должно быть от 0 до 100000.",
        "invalid_water": "Неверное количество воды. Пожалуйста, введи значение от 0.1 до 100 литров.",
        "calories_mismatch": "Сумма калорий из белков, жиров и углеводов не совпадает с указанными калориями.",
        "water_added": "Ты добавил {water} литров воды.",
        "food_added": "Ты добавил еду с {calories} калориями.",
        "invalid_timezone": "Неверный формат часового пояса. Используй формат UTC±HH или UTC±HH:MM. Примеры: UTC+03, UTC-02, UTC+05:30.",
        "timezone_set": "Часовой пояс установлен на {timezone}.",
        "invalid_language": "Неверный язык. Доступны только 'en' и 'ru'.",
        "language_changed": "Язык изменен на {language}.",
        "no_data_for_date": "Нет данных за указанную дату.",
        "invalid_comment": "Комментарий должен быть меньше 100 символов.",
        "error_occurred": "Произошла ошибка.",
        "set_info_usage": "Использование: /set <калории> <белки> <жиры> <углеводы> <вода>. Пример: /set 2000 150 50 250 2.5",
        "add_food_usage": (
            "Использование: /food <съеденные_граммы> <белки_на_100г> <жиры_на_100г> <углеводы_на_100г> [комментарий].\n"
            "Пример: /food 150 10 5 20 Вкусная каша."
        ),
        "set_timezone_usage": "Использование: /time <часовой пояс>. Примеры: /time UTC+03, /time UTC-05:30",
        "set_language_usage": "Использование: /lang <en/ru>. Пример: /lang ru",
        "add_water_usage": "Использование: /water <литры>. Пример: /water 2.5",
        "get_daily_log_usage": "Использование: /log [дата]. Пример: /log 2023-10-15",
        "invalid_date_format": "Неверный формат даты. Пожалуйста, используй формат ГГГГ-ММ-ДД.",
        "food_entry": "[{time}] Еда: {calories} ккал, Б: {protein}, Ж: {fat}, У: {carbohydrates}, Комментарий: {comment}",
        "water_entry": "[{time}] Вода: {water} литров",
        "calculate_info_usage": (
            "Использование: /calc <возраст> <вес> <рост> <метаболизм> <активность> <цель> <желание> <тип_диеты> <пол> <жирность_тела> <климат> <пульс_в_покое>.\n\n"
            "Параметры:\n"
            "- возраст: Целое число от 1 до 200.\n"
            "- вес: Число с плавающей точкой от 1 до 1000 (кг).\n"
            "- рост: Число с плавающей точкой от 1 до 1000 (см).\n"
            "- метаболизм: Целое число от 1 до 10 или '-' (опционально).\n"
            "- активность: Целое число от 0 до 10 или '-' (опционально).\n"
            "- цель: Целое число -1 (похудеть), 0 (поддерживать вес), +1 (набрать вес), или '-' (опционально).\n"
            "- желание: Целое число от 1 до 10 или '-' (насколько сильно ты хочешь похудеть/набрать вес). Если '-', не будет учитываться.\n"
            "- тип_диеты: Целое число 0 (базовая), 1 (белковая), 2 (жирная), 3 (углеводистая), или '-' (опционально).\n"
            "- пол: 'm' для мужского, 'f' для женского или '-' (опционально).\n"
            "- жирность_тела: Число с плавающей точкой от 0.1 до 100 или '-' (опционально).\n"
            "- климат: Целое число -1 (холодный), 0 (влажный), 1 (жаркий), или '-' (опционально).\n"
            "- пульс_в_покое: Целое число от 40 до 140 или '-' (опционально).\n\n"
            "Примеры:\n"
            "/calc 30 70 175 5 5 -1 7 1 m 20 0 70\n"
            "/calc 25 60 160 - - - - 0 - - -"
        ),
        "invalid_age": "Неверный возраст. Пожалуйста, введи значение от 1 до 200.",
        "invalid_weight": "Неверный вес. Пожалуйста, введи значение от 1 до 1000.",
        "invalid_height": "Неверный рост. Пожалуйста, введи значение от 1 до 1000.",
        "invalid_metabolism": "Неверный метаболизм. Пожалуйста, введи значение от 1 до 10, или '-' если опционально.",
        "invalid_activity": "Неверная активность. Пожалуйста, введи значение от 0 до 10, или '-' если опционально.",
        "invalid_goal": "Неверная цель. Пожалуйста, введи -1 для похудения, 0 для поддержания или +1 для набора веса, или '-' если опционально.",
        "invalid_desire": "Неверное желание. Пожалуйста, введи значение от 1 до 10 или '-' если ты не хочешь менять вес.",
        "invalid_diet_type": "Неверный тип диеты. Пожалуйста, введи 0 для базовой, 1 для белковой, 2 для жирной или 3 для углеводистой диеты, или '-' если опционально.",
        "invalid_gender": "Неверный пол. Пожалуйста, введи 'm' для мужского, 'f' для женского или '-' если опционально.",
        "invalid_body_fat": "Неверный процент жира в теле. Введи значение от 0.1 до 100 или '-' если не применяется.",
        "invalid_climate": "Неверное значение климата. Пожалуйста, введи -1 для холодного, 0 для влажного или +1 для жаркого, или '-' если опционально.",
        "invalid_rhr": "Неверный пульс в покое. Введи значение от 40 до 140, или '-' если не применяется.",
        "auto_update_info": "Исходя из твоих данных, пожалуйста, используй следующую команду для обновления информации:\n{command}",
        "current_info_message": (
            "Текущие данные:\n"
            "Калории: {calories} ккал\n"
            "Белки: {protein} г\n"
            "Жиры: {fat} г\n"
            "Углеводы: {carbohydrates} г\n"
            "Вода: {water} литров"
        ),
        "daily_progress_message": (
            "Дневной прогресс на {date}:\n"
            "Съедено: {calories_eaten} из {calories_total} ккал\n"
            "Осталось: {calories_remaining} ккал\n\n"
            "Белки: {protein_eaten} из {protein_total} г (осталось: {protein_remaining} г)\n"
            "Жиры: {fat_eaten} из {fat_total} г (осталось: {fat_remaining} г)\n"
            "Углеводы: {carbs_eaten} из {carbs_total} г (осталось: {carbs_remaining} г)\n\n"
            "Вода: выпито {water_drank} из {water_total} литров (осталось: {water_remaining} литров)"
        ),
        "daily_food_and_water_log": "Подробный отчет о потреблении пищи и воды за {date}:",
        "get_daily_progress_usage": "Использование: /progress [дата]. Пример: /progress 2023-10-15",
        "user_count_message": "Общее количество пользователей: {count}.",
        "invalid_grams_eaten": "Неверное количество грамм. Пожалуйста, введи значение от 1 до 100000 грамм.",
        "invalid_macros": "Неверные значения для белков, жиров или углеводов. Каждое должно быть от 0 до 100000.",
        "no_non_zero_macro": "Хотя бы одно из значений белков, жиров или углеводов должно быть больше нуля.",
    },
}


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    timezone = Column(String, default="UTC", nullable=False)
    language = Column(String, default="en", nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class InfoLog(Base):
    __tablename__ = "info_log"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    calories = Column(Float, default=0.0, nullable=False)
    protein = Column(Float, default=0.0, nullable=False)
    fat = Column(Float, default=0.0, nullable=False)
    carbohydrates = Column(Float, default=0.0, nullable=False)
    water = Column(Float, default=0.0, nullable=False)
    date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class FoodLog(Base):
    __tablename__ = "food_log"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    calories = Column(Float, default=0.0, nullable=False)
    protein = Column(Float, default=0.0, nullable=False)
    fat = Column(Float, default=0.0, nullable=False)
    carbohydrates = Column(Float, default=0.0, nullable=False)
    comment = Column(String, default="", nullable=False)


class WaterLog(Base):
    __tablename__ = "water_log"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    water = Column(Float, default=0.0, nullable=False)


class DailySummary(Base):
    __tablename__ = "daily_summary"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    total_calories = Column(Float, default=0.0, nullable=False)
    total_protein = Column(Float, default=0.0, nullable=False)
    total_fat = Column(Float, default=0.0, nullable=False)
    total_carbohydrates = Column(Float, default=0.0, nullable=False)
    total_water = Column(Float, default=0.0, nullable=False)


@asynccontextmanager
async def get_db_session():
    async with async_session() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def get_translation(user_language, key, **kwargs):
    for k, v in kwargs.items():
        if isinstance(v, (int, float)):
            kwargs[k] = round_value(v)

    try:
        message = translations[user_language][key].format(**kwargs)
    except KeyError:
        message = translations["en"][key].format(**kwargs)
    return message


async def on_startup(dispatcher):
    await init_db()


def get_utc_now():
    return datetime.now(pytz.utc)


def round_value(value):
    if isinstance(value, float):
        return round(value, 1)
    return value


def get_user_timezone(timezone_str: str):
    excluded_timezones = ["UTC", "UTC+00", "UTC-00"]
    if timezone_str in excluded_timezones:
        return pytz.utc
    elif timezone_str.startswith("UTC"):
        try:
            match = re.match(r"^UTC([+-])(\d{2})(?::(\d{2}))?$", timezone_str)
            if not match:
                raise ValueError("Invalid timezone format.")

            sign, hours, minutes = match.groups()
            hours = int(hours)
            minutes = int(minutes) if minutes else 0

            if hours > 14 or minutes >= 60:
                raise ValueError("Invalid timezone offset values.")

            total_minutes = hours * 60 + minutes
            if sign == "-":
                total_minutes = -total_minutes

            return pytz.FixedOffset(total_minutes)
        except ValueError as e:
            logger.debug(
                f"Invalid timezone format: {timezone_str}. Error: {e}. Defaulting to UTC."
            )
            return pytz.utc
    else:
        logger.debug(f"Unsupported timezone format: {timezone_str}. Defaulting to UTC.")
        return pytz.utc


def convert_to_user_timezone(utc_time, timezone_str):
    user_timezone = get_user_timezone(timezone_str)
    return utc_time.astimezone(user_timezone)


async def get_or_create_user(session, telegram_id: int):
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    user = result.scalars().first()
    if not user:
        user = User(telegram_id=telegram_id)
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


async def handle_error(message: types.Message):
    async with get_db_session() as session:
        stmt = select(User).where(User.telegram_id == message.from_user.id)
        result = await session.execute(stmt)
        user = result.scalars().first()
        user_language = (
            user.language if user and user.language in translations else "en"
        )
        error_message = get_translation(user_language, "error_occurred")
        await message.reply(error_message)


@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    logger.debug(f"User {message.from_user.id} issued /start command.")
    async with get_db_session() as session:
        user = await get_or_create_user(session, message.from_user.id)
        await message.reply(get_translation(user.language, "start"))


@dp.message_handler(commands=["set"])
async def set_info(message: types.Message):
    logger.debug(
        f"User {message.from_user.id} issued /set command with data: {message.text}"
    )
    try:
        async with get_db_session() as session:
            user = await get_or_create_user(session, message.from_user.id)
            data = message.text.split(" ")[1:]
            if len(data) != 5:
                await message.reply(get_translation(user.language, "set_info_usage"))
                return

            try:
                calories = float(data[0])
            except ValueError:
                await message.reply(get_translation(user.language, "invalid_calories"))
                return

            try:
                protein = float(data[1])
                fat = float(data[2])
                carbs = float(data[3])
            except ValueError:
                await message.reply(
                    get_translation(user.language, "invalid_protein_fat_carbs")
                )
                return

            try:
                water = float(data[4])
            except ValueError:
                await message.reply(get_translation(user.language, "invalid_water"))
                return

            total_calories = (protein * 4) + (fat * 9) + (carbs * 4)
            if abs(total_calories - calories) > 10:
                await message.reply(get_translation(user.language, "calories_mismatch"))
                return

            if not (10 <= calories <= 100000):
                await message.reply(get_translation(user.language, "invalid_calories"))
                return
            if not (
                0 <= protein <= 100000 and 0 <= fat <= 100000 and 0 <= carbs <= 100000
            ):
                await message.reply(
                    get_translation(user.language, "invalid_protein_fat_carbs")
                )
                return
            if not (0.1 <= water <= 100):
                await message.reply(get_translation(user.language, "invalid_water"))
                return

            current_time = get_utc_now()

            info_log = InfoLog(
                user_id=user.id,
                calories=calories,
                protein=protein,
                fat=fat,
                carbohydrates=carbs,
                water=water,
                date=current_time,
            )
            session.add(info_log)
            await session.commit()

            await message.reply(get_translation(user.language, "data_updated"))
    except Exception as e:
        logger.debug(f"Error in set_info: {e}")
        await handle_error(message)


@dp.message_handler(commands=["food"])
async def add_food(message: types.Message):
    logger.debug(
        f"User {message.from_user.id} issued /food command with data: {message.text}"
    )
    try:
        async with get_db_session() as session:
            user = await get_or_create_user(session, message.from_user.id)

            data = message.text.split(" ")[1:]
            if len(data) < 4:
                await message.reply(get_translation(user.language, "add_food_usage"))
                return

            try:
                grams_eaten = float(data[0])
                if not (1 <= grams_eaten <= 100000):
                    await message.reply(
                        get_translation(user.language, "invalid_grams_eaten")
                    )
                    return
            except ValueError:
                await message.reply(
                    get_translation(user.language, "invalid_grams_eaten")
                )
                return

            try:
                protein_per_100g = float(data[1])
                fat_per_100g = float(data[2])
                carbs_per_100g = float(data[3])
                if not (
                    0 <= protein_per_100g <= 100000
                    and 0 <= fat_per_100g <= 100000
                    and 0 <= carbs_per_100g <= 100000
                ):
                    await message.reply(
                        get_translation(user.language, "invalid_macros")
                    )
                    return
                if not (protein_per_100g > 0 or fat_per_100g > 0 or carbs_per_100g > 0):
                    await message.reply(
                        get_translation(user.language, "no_non_zero_macro")
                    )
                    return
            except ValueError:
                await message.reply(get_translation(user.language, "invalid_macros"))
                return

            comment = " ".join(data[4:]) if len(data) > 4 else ""

            protein = (protein_per_100g * grams_eaten) / 100
            fat = (fat_per_100g * grams_eaten) / 100
            carbs = (carbs_per_100g * grams_eaten) / 100
            calories = (protein * 4) + (fat * 9) + (carbs * 4)

            if len(comment) > 100:
                await message.reply(get_translation(user.language, "invalid_comment"))
                return

            current_time = get_utc_now()
            food_log = FoodLog(
                user_id=user.id,
                calories=calories,
                protein=protein,
                fat=fat,
                carbohydrates=carbs,
                comment=comment,
                date=current_time,
            )
            session.add(food_log)

            target_date = convert_to_user_timezone(current_time, user.timezone).date()

            stmt = select(DailySummary).where(
                DailySummary.user_id == user.id,
                func.date(DailySummary.date) == target_date,
            )
            result = await session.execute(stmt)
            daily_summary = result.scalars().first()
            if not daily_summary:
                daily_summary = DailySummary(
                    user_id=user.id,
                    date=current_time,
                    total_calories=0.0,
                    total_protein=0.0,
                    total_fat=0.0,
                    total_carbohydrates=0.0,
                    total_water=0.0,
                )
                session.add(daily_summary)

            daily_summary.total_calories += calories
            daily_summary.total_protein += protein
            daily_summary.total_fat += fat
            daily_summary.total_carbohydrates += carbs

            await session.commit()

            await message.reply(
                get_translation(
                    user.language, "food_added", calories=round_value(calories)
                )
            )
    except Exception as e:
        logger.debug(f"Error in add_food: {e}")
        await handle_error(message)


@dp.message_handler(commands=["water"])
async def add_water(message: types.Message):
    logger.debug(
        f"User {message.from_user.id} issued /water command with data: {message.text}"
    )
    try:
        async with get_db_session() as session:
            user = await get_or_create_user(session, message.from_user.id)

            data = message.text.split(" ")
            if len(data) != 2:
                await message.reply(get_translation(user.language, "add_water_usage"))
                return

            try:
                water = float(data[1])
                if not (0.1 <= water <= 100):
                    await message.reply(get_translation(user.language, "invalid_water"))
                    return
            except ValueError:
                await message.reply(get_translation(user.language, "invalid_water"))
                return

            current_time = get_utc_now()
            water_log = WaterLog(user_id=user.id, water=water, date=current_time)
            session.add(water_log)

            target_date = convert_to_user_timezone(current_time, user.timezone).date()

            stmt = select(DailySummary).where(
                DailySummary.user_id == user.id,
                func.date(DailySummary.date) == target_date,
            )
            result = await session.execute(stmt)
            daily_summary = result.scalars().first()
            if not daily_summary:
                daily_summary = DailySummary(
                    user_id=user.id,
                    date=current_time,
                    total_calories=0.0,
                    total_protein=0.0,
                    total_fat=0.0,
                    total_carbohydrates=0.0,
                    total_water=0.0,
                )
                session.add(daily_summary)

            daily_summary.total_water += water
            await session.commit()

            await message.reply(
                get_translation(user.language, "water_added", water=round_value(water))
            )
    except Exception as e:
        logger.debug(f"Error in add_water: {e}")
        await handle_error(message)


@dp.message_handler(commands=["time"])
async def set_timezone(message: types.Message):
    logger.debug(
        f"User {message.from_user.id} issued /time command with data: {message.text}"
    )
    try:
        async with get_db_session() as session:
            user = await get_or_create_user(session, message.from_user.id)

            data = message.text.split(" ")
            if len(data) != 2:
                await message.reply(
                    get_translation(user.language, "set_timezone_usage")
                )
                return

            timezone = data[1]
            if not re.match(r"^UTC([+-]\d{2}(?::\d{2})?)?$", timezone):
                await message.reply(get_translation(user.language, "invalid_timezone"))
                return

            user.timezone = timezone
            await session.commit()
            await message.reply(
                get_translation(user.language, "timezone_set", timezone=timezone)
            )
    except Exception as e:
        logger.debug(f"Error in set_timezone: {e}")
        await handle_error(message)


@dp.message_handler(commands=["lang"])
async def set_language(message: types.Message):
    logger.debug(
        f"User {message.from_user.id} issued /lang command with data: {message.text}"
    )
    try:
        async with get_db_session() as session:
            user = await get_or_create_user(session, message.from_user.id)

            data = message.text.split(" ")
            if len(data) != 2 or data[1] not in ["en", "ru"]:
                await message.reply(
                    get_translation(user.language, "set_language_usage")
                )
                return

            language = data[1]
            user.language = language
            await session.commit()
            await message.reply(
                get_translation(language, "language_changed", language=language)
            )
    except Exception as e:
        logger.debug(f"Error in set_language: {e}")
        await handle_error(message)


@dp.message_handler(commands=["log"])
async def get_daily_log(message: types.Message):
    logger.debug(
        f"User {message.from_user.id} issued /log command with data: {message.text}"
    )

    try:
        async with get_db_session() as session:
            user = await get_or_create_user(session, message.from_user.id)

            data = message.text.split(" ")
            if len(data) == 1:
                target_date = convert_to_user_timezone(
                    get_utc_now(), user.timezone
                ).date()
            elif len(data) == 2:
                try:
                    target_date = datetime.strptime(data[1], "%Y-%m-%d").date()
                except ValueError:
                    await message.reply(
                        get_translation(user.language, "invalid_date_format")
                    )
                    return
            else:
                await message.reply(
                    get_translation(user.language, "get_daily_log_usage")
                )
                return

            user_timezone_str = user.timezone
            user_timezone = get_user_timezone(user_timezone_str)

            start_datetime = user_timezone.localize(
                datetime.combine(target_date, time.min)
            ).astimezone(pytz.utc)
            end_datetime = user_timezone.localize(
                datetime.combine(target_date, time.max)
            ).astimezone(pytz.utc)

            food_stmt = select(FoodLog).where(
                FoodLog.user_id == user.id,
                FoodLog.date >= start_datetime,
                FoodLog.date <= end_datetime,
            )

            water_stmt = select(WaterLog).where(
                WaterLog.user_id == user.id,
                WaterLog.date >= start_datetime,
                WaterLog.date <= end_datetime,
            )
            food_logs = await session.execute(food_stmt)
            water_logs = await session.execute(water_stmt)

            combined_logs = []

            for log in food_logs.scalars().all():
                combined_logs.append({"type": "food", "date": log.date, "data": log})

            for log in water_logs.scalars().all():
                combined_logs.append({"type": "water", "date": log.date, "data": log})

            combined_logs.sort(key=lambda x: x["date"])

            formatted_entries = []
            for entry in combined_logs:
                log_time_utc = entry["date"]
                local_time = convert_to_user_timezone(log_time_utc, user.timezone)

                if user.language == "en":
                    time_str = local_time.strftime("%I:%M %p")
                else:
                    time_str = local_time.strftime("%H:%M")

                if entry["type"] == "food":
                    log = entry["data"]
                    formatted_entries.append(
                        get_translation(
                            user.language,
                            "food_entry",
                            time=time_str,
                            calories=round_value(log.calories),
                            protein=round_value(log.protein),
                            fat=round_value(log.fat),
                            carbohydrates=round_value(log.carbohydrates),
                            comment=log.comment if log.comment else "-",
                        )
                    )
                elif entry["type"] == "water":
                    log = entry["data"]
                    formatted_entries.append(
                        get_translation(
                            user.language,
                            "water_entry",
                            time=time_str,
                            water=round_value(log.water),
                        )
                    )

            if formatted_entries:
                header = get_translation(
                    user.language, "daily_food_and_water_log", date=target_date
                )
                all_data = "\n".join(formatted_entries)
                message_text = f"{header}\n{all_data}"
                while message_text:
                    part, message_text = message_text[:4096], message_text[4096:]
                    await message.reply(part)
            else:
                await message.reply(get_translation(user.language, "no_data_for_date"))

    except Exception as e:
        logger.debug(f"Error in get_daily_log: {e}")
        await handle_error(message)


@dp.message_handler(commands=["calc"])
async def calculate_info(message: types.Message):
    logger.debug(
        f"User {message.from_user.id} issued /calc command with data: {message.text}"
    )

    try:
        async with get_db_session() as session:
            user = await get_or_create_user(session, message.from_user.id)
            user_language = (
                user.language if user and user.language in translations else "en"
            )

            data = message.text.split(" ")[1:]
            if len(data) != 12:
                await message.reply(
                    get_translation(user_language, "calculate_info_usage")
                )
                return

            try:
                age = int(data[0])
                if not (1 <= age <= 200):
                    await message.reply(get_translation(user_language, "invalid_age"))
                    return
            except ValueError:
                await message.reply(get_translation(user_language, "invalid_age"))
                return

            try:
                weight = float(data[1])
                if not (1 <= weight <= 1000):
                    await message.reply(
                        get_translation(user_language, "invalid_weight")
                    )
                    return
            except ValueError:
                await message.reply(get_translation(user_language, "invalid_weight"))
                return

            try:
                height = float(data[2])
                if not (1 <= height <= 300):
                    await message.reply(
                        get_translation(user_language, "invalid_height")
                    )
                    return
            except ValueError:
                await message.reply(get_translation(user_language, "invalid_height"))
                return

            metabolism_input = data[3]
            if metabolism_input == "-":
                metabolism = None
            else:
                try:
                    metabolism = int(metabolism_input)
                    if not (1 <= metabolism <= 10):
                        await message.reply(
                            get_translation(user_language, "invalid_metabolism")
                        )
                        return
                except ValueError:
                    await message.reply(
                        get_translation(user_language, "invalid_metabolism")
                    )
                    return

            activity_input = data[4]
            if activity_input == "-":
                activity = 0
            else:
                try:
                    activity = int(activity_input)
                    if not (0 <= activity <= 10):
                        await message.reply(
                            get_translation(user_language, "invalid_activity")
                        )
                        return
                except ValueError:
                    await message.reply(
                        get_translation(user_language, "invalid_activity")
                    )
                    return

            goal_input = data[5]
            if goal_input == "-":
                goal = 0
            else:
                try:
                    goal = int(goal_input)
                    if goal not in [-1, 0, 1]:
                        await message.reply(
                            get_translation(user_language, "invalid_goal")
                        )
                        return
                except ValueError:
                    await message.reply(get_translation(user_language, "invalid_goal"))
                    return

            desire_input = data[6].lower()
            if desire_input == "-":
                desire = None
            else:
                try:
                    desire = int(desire_input)
                    if not (1 <= desire <= 10):
                        await message.reply(
                            get_translation(user_language, "invalid_desire")
                        )
                        return
                except ValueError:
                    await message.reply(
                        get_translation(user_language, "invalid_desire")
                    )
                    return

            diet_type_input = data[7]
            if diet_type_input == "-":
                diet_type = 0
            else:
                try:
                    diet_type = int(diet_type_input)
                    if diet_type not in [0, 1, 2, 3]:
                        await message.reply(
                            get_translation(user_language, "invalid_diet_type")
                        )
                        return
                except ValueError:
                    await message.reply(
                        get_translation(user_language, "invalid_diet_type")
                    )
                    return

            gender_input = data[8].lower()
            if gender_input == "-":
                gender = None
            elif gender_input in ["m", "f"]:
                gender = gender_input
            else:
                await message.reply(get_translation(user_language, "invalid_gender"))
                return

            body_fat_input = data[9].lower()
            if body_fat_input == "-":
                body_fat = None
            else:
                try:
                    body_fat = float(body_fat_input)
                    if not (0.1 <= body_fat <= 100):
                        await message.reply(
                            get_translation(user_language, "invalid_body_fat")
                        )
                        return
                except ValueError:
                    await message.reply(
                        get_translation(user_language, "invalid_body_fat")
                    )
                    return

            climate_input = data[10]
            if climate_input == "-":
                climate = 0
            else:
                try:
                    climate = int(climate_input)
                    if climate not in [-1, 0, 1]:
                        await message.reply(
                            get_translation(user_language, "invalid_climate")
                        )
                        return
                except ValueError:
                    await message.reply(
                        get_translation(user_language, "invalid_climate")
                    )
                    return

            rhr_input = data[11].lower()
            if rhr_input == "-":
                resting_heart_rate = None
            else:
                try:
                    resting_heart_rate = int(rhr_input)
                    if not (40 <= resting_heart_rate <= 140):
                        await message.reply(
                            get_translation(user_language, "invalid_rhr")
                        )
                        return
                except ValueError:
                    await message.reply(get_translation(user_language, "invalid_rhr"))
                    return

            metabolism_adjustment = 0.95 if age > 60 else 1.0

            menopause_adjustment = 0.9 if gender == "f" and age >= 50 else 1.0

            heart_rate_adjustment = (
                70 / resting_heart_rate if resting_heart_rate else 1.0
            )

            if gender is None:
                bmr_mifflin_m = 10 * weight + 6.25 * height - 5 * age + 5
                bmr_mifflin_f = 10 * weight + 6.25 * height - 5 * age - 161
                bmr_mifflin = (bmr_mifflin_m + bmr_mifflin_f) / 2

                bmr_harris_m = (
                    66.5 + (13.75 * weight) + (5.003 * height) - (6.775 * age)
                )
                bmr_harris_f = (
                    655.1 + (9.563 * weight) + (1.85 * height) - (4.676 * age)
                )
                bmr_harris = (bmr_harris_m + bmr_harris_f) / 2
            elif gender == "m":
                bmr_mifflin = 10 * weight + 6.25 * height - 5 * age + 5
                bmr_harris = 66.5 + (13.75 * weight) + (5.003 * height) - (6.775 * age)
            else:
                bmr_mifflin = 10 * weight + 6.25 * height - 5 * age - 161
                bmr_harris = 655.1 + (9.563 * weight) + (1.85 * height) - (4.676 * age)

            bmr = (bmr_mifflin + bmr_harris) / 2

            if metabolism is not None:
                metabolism_coefficient = 0.95 + (metabolism - 1) * 0.01
                metabolism_coefficient = min(max(metabolism_coefficient, 0.95), 1.05)
                bmr *= metabolism_coefficient

            bmr *= metabolism_adjustment * menopause_adjustment * heart_rate_adjustment

            activity_factor = 1.2 + 0.1 * activity if activity <= 9 else 1.9
            tdee = bmr * activity_factor

            if goal == -1 and desire is not None:
                tdee -= 500 * (desire / 10)
            elif goal == 1 and desire is not None:
                tdee += 500 * (desire / 10)

            if diet_type == 0:
                protein_percent, fat_percent, carbs_percent = 20, 30, 50
            elif diet_type == 1:
                protein_percent, fat_percent, carbs_percent = 45, 30, 25
            elif diet_type == 2:
                protein_percent, fat_percent, carbs_percent = 15, 75, 10
            elif diet_type == 3:
                protein_percent, fat_percent, carbs_percent = 15, 25, 60

            protein_cal = tdee * (protein_percent / 100)
            fat_cal = tdee * (fat_percent / 100)
            carbs_cal = tdee * (carbs_percent / 100)

            protein_grams = round(protein_cal / 4)
            fat_grams = round(fat_cal / 9)
            carbs_grams = round((tdee - (protein_grams * 4 + fat_grams * 9)) / 4)

            climate_multiplier = 0.8 if climate == -1 else 1.2 if climate == 1 else 1.0
            water_multiplier = (
                1.0 + (activity * 0.05)
                if activity <= 3
                else 1.25 + ((activity - 6) * 0.15)
            )
            water = min(
                100, round(weight * 0.035 * climate_multiplier * water_multiplier, 1)
            )

            update_command = f"/set {round_value(int(tdee))} {round_value(protein_grams)} {round_value(fat_grams)} {round_value(carbs_grams)} {round_value(water)}"
            auto_update_message = get_translation(
                user_language,
                "auto_update_info",
                command=f"```copy\n{update_command}\n```",
            )
            await message.reply(auto_update_message, parse_mode="Markdown")
    except Exception as e:
        logger.debug(f"Error in calculate_info: {e}")
        await handle_error(message)


@dp.message_handler(commands=["get"])
async def get_info(message: types.Message):
    logger.debug(f"User {message.from_user.id} issued /get command.")
    try:
        async with get_db_session() as session:
            user = await get_or_create_user(session, message.from_user.id)

            stmt = (
                select(InfoLog)
                .where(InfoLog.user_id == user.id)
                .order_by(InfoLog.date.desc())
                .limit(1)
            )
            result = await session.execute(stmt)
            info_log = result.scalars().first()

            if not info_log:
                await message.reply(get_translation(user.language, "enter_data_first"))
                return

            info_message = get_translation(
                user.language,
                "current_info_message",
                calories=round_value(info_log.calories),
                protein=round_value(info_log.protein),
                fat=round_value(info_log.fat),
                carbohydrates=round_value(info_log.carbohydrates),
                water=round_value(info_log.water),
            )
            await message.reply(info_message)
    except Exception as e:
        logger.debug(f"Error in get_info: {e}")
        await handle_error(message)


@dp.message_handler(commands=["count"])
async def user_count(message: types.Message):
    logger.debug(f"User {message.from_user.id} issued /count command.")

    try:
        async with get_db_session() as session:
            stmt = select(func.count(User.id))
            result = await session.execute(stmt)
            user_count = result.scalar()

            user = await get_or_create_user(session, message.from_user.id)
            user_language = (
                user.language if user and user.language in translations else "en"
            )

            await message.reply(
                get_translation(user_language, "user_count_message", count=user_count)
            )
    except Exception as e:
        logger.debug(f"Error in user_count: {e}")
        await handle_error(message)


@dp.message_handler(commands=["progress"])
async def get_daily_progress(message: types.Message):
    logger.debug(f"User {message.from_user.id} issued /progress command.")

    try:
        async with get_db_session() as session:
            user = await get_or_create_user(session, message.from_user.id)
            user_language = (
                user.language if user and user.language in translations else "en"
            )
            data = message.text.split(" ")
            if len(data) == 1:
                target_date = convert_to_user_timezone(
                    get_utc_now(), user.timezone
                ).date()
            elif len(data) == 2:
                try:
                    target_date = datetime.strptime(data[1], "%Y-%m-%d").date()
                except ValueError:
                    await message.reply(
                        get_translation(user_language, "invalid_date_format")
                    )
                    return
            else:
                await message.reply(
                    get_translation(user_language, "get_daily_progress_usage")
                )
                return

            user_timezone_str = user.timezone
            user_timezone = get_user_timezone(user_timezone_str)

            start_datetime = user_timezone.localize(
                datetime.combine(target_date, time.min)
            ).astimezone(pytz.utc)
            end_datetime = user_timezone.localize(
                datetime.combine(target_date, time.max)
            ).astimezone(pytz.utc)

            stmt_info = (
                select(InfoLog)
                .where(
                    InfoLog.user_id == user.id,
                    InfoLog.date >= start_datetime,
                    InfoLog.date <= end_datetime,
                )
                .order_by(InfoLog.date.desc())
                .limit(1)
            )
            result_info = await session.execute(stmt_info)
            info_log = result_info.scalars().first()

            if not info_log:
                await message.reply(get_translation(user_language, "no_data_for_date"))
                return

            stmt_summary = select(DailySummary).where(
                DailySummary.user_id == user.id,
                DailySummary.date >= start_datetime,
                DailySummary.date <= end_datetime,
            )
            result_summary = await session.execute(stmt_summary)
            daily_summary = result_summary.scalars().first()

            if not daily_summary:
                await message.reply(get_translation(user_language, "no_data_for_date"))
                return

            calories_total = info_log.calories
            protein_total = info_log.protein
            fat_total = info_log.fat
            carbs_total = info_log.carbohydrates
            water_total = info_log.water

            calories_eaten = daily_summary.total_calories
            protein_eaten = daily_summary.total_protein
            fat_eaten = daily_summary.total_fat
            carbs_eaten = daily_summary.total_carbohydrates
            water_drank = daily_summary.total_water

            calories_remaining = max(0, calories_total - calories_eaten)
            protein_remaining = max(0, protein_total - protein_eaten)
            fat_remaining = max(0, fat_total - fat_eaten)
            carbs_remaining = max(0, carbs_total - carbs_eaten)
            water_remaining = max(0, water_total - water_drank)

            progress_message = get_translation(
                user_language,
                "daily_progress_message",
                date=target_date,
                calories_eaten=round_value(calories_eaten),
                calories_total=round_value(calories_total),
                calories_remaining=round_value(calories_remaining),
                protein_eaten=round_value(protein_eaten),
                protein_total=round_value(protein_total),
                protein_remaining=round_value(protein_remaining),
                fat_eaten=round_value(fat_eaten),
                fat_total=round_value(fat_total),
                fat_remaining=round_value(fat_remaining),
                carbs_eaten=round_value(carbs_eaten),
                carbs_total=round_value(carbs_total),
                carbs_remaining=round_value(carbs_remaining),
                water_drank=round_value(water_drank),
                water_total=round_value(water_total),
                water_remaining=round_value(water_remaining),
            )

            await message.reply(progress_message)

    except Exception as e:
        logger.debug(f"Error in get_daily_progress: {e}")
        await handle_error(message)


@dp.message_handler(commands=["reset"])
async def reset_daily_progress(message: types.Message):
    logger.debug(f"User {message.from_user.id} issued /reset command.")
    try:
        async with get_db_session() as session:
            user = await get_or_create_user(session, message.from_user.id)

            current_time = get_utc_now()
            target_date = convert_to_user_timezone(current_time, user.timezone).date()

            user_timezone_str = user.timezone
            user_timezone = get_user_timezone(user_timezone_str)

            start_datetime = user_timezone.localize(
                datetime.combine(target_date, time.min)
            ).astimezone(pytz.utc)
            end_datetime = user_timezone.localize(
                datetime.combine(target_date, time.max)
            ).astimezone(pytz.utc)

            await session.execute(
                delete(FoodLog)
                .where(
                    FoodLog.user_id == user.id,
                    FoodLog.date >= start_datetime,
                    FoodLog.date <= end_datetime,
                )
                .execution_options(synchronize_session=False)
            )
            await session.execute(
                delete(WaterLog)
                .where(
                    WaterLog.user_id == user.id,
                    WaterLog.date >= start_datetime,
                    WaterLog.date <= end_datetime,
                )
                .execution_options(synchronize_session=False)
            )
            await session.execute(
                delete(InfoLog)
                .where(
                    InfoLog.user_id == user.id,
                    InfoLog.date >= start_datetime,
                    InfoLog.date <= end_datetime,
                )
                .execution_options(synchronize_session=False)
            )
            await session.commit()

            stmt = select(DailySummary).where(
                DailySummary.user_id == user.id,
                DailySummary.date >= start_datetime,
                DailySummary.date <= end_datetime,
            )
            result = await session.execute(stmt)
            daily_summary = result.scalars().first()

            if daily_summary:
                daily_summary.total_calories = 0.0
                daily_summary.total_protein = 0.0
                daily_summary.total_fat = 0.0
                daily_summary.total_carbohydrates = 0.0
                daily_summary.total_water = 0.0
            else:
                daily_summary = DailySummary(
                    user_id=user.id,
                    date=current_time,
                    total_calories=0.0,
                    total_protein=0.0,
                    total_fat=0.0,
                    total_carbohydrates=0.0,
                    total_water=0.0,
                )
                session.add(daily_summary)

            await session.commit()
            await message.reply(get_translation(user.language, "data_updated"))

    except Exception as e:
        logger.debug(f"Error in reset_daily_progress: {e}")
        await handle_error(message)


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
