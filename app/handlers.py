import sqlite3
from datetime import datetime
from io import BytesIO

import aiohttp
import matplotlib.pyplot as plt
from aiogram import Bot
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from config import TOKEN

router = Router()


# Обработчик команды /start
@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.reply("Добро пожаловать! Я ваш бот.\nВведите /help для списка команд.")


# Обработчик команды /help
@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.reply(
        "Доступные команды:\n"
        "/start - Начало работы\n"
        "/set_profile - Настроить профиль (вес, рост, возраст, активность, город и цель калорий)\n"
        "/profile- Получить информацию о своем профиле\n"
        "/log_water-логирование воды\n"
        "/log_food - лог каллорий\n"
        "/log_workout - логирование тренировок\n"
        "/check_progress - за текущий день кол-во выпитого и наеденного\n"
        "/show_progress - график прогресса"
    )


#############################################################################################################


class ProfileForm(StatesGroup):
    nickname = State()
    weight = State()
    height = State()
    age = State()
    activity_level = State()
    city = State()
    gender = State()
    calorie_goal = State()
    water_goal = State()


# Команда /set_profile, которая запускает процесс настройки профиля
@router.message(Command("set_profile"))
async def set_profile(message: Message, state: FSMContext):
    await message.reply("Введите ваш вес (в кг):")
    await state.set_state(ProfileForm.weight)  # Переход к следующему состоянию


# Обработчик ввода веса
@router.message(ProfileForm.weight)
async def process_weight(message: Message, state: FSMContext):
    weight = message.text.strip()

    if not weight.isdigit():
        await message.reply("Пожалуйста, введите корректное число для веса.")
        return

    weight = int(weight)
    await state.update_data(weight=weight)

    await message.reply("Введите ваш рост (в см):")
    await state.set_state(ProfileForm.height)  # Переход к следующему состоянию


# Обработчик ввода роста
@router.message(ProfileForm.height)
async def process_height(message: Message, state: FSMContext):
    height = message.text.strip()

    if not height.isdigit():
        await message.reply("Пожалуйста, введите корректное число для роста.")
        return

    height = int(height)
    await state.update_data(height=height)

    await message.reply("Введите ваш возраст:")
    await state.set_state(ProfileForm.age)  # Переход к следующему состоянию


# Обработчик ввода возраста
@router.message(ProfileForm.age)
async def process_age(message: Message, state: FSMContext):
    age = message.text.strip()

    if not age.isdigit():
        await message.reply("Пожалуйста, введите корректное число для возраста.")
        return

    age = int(age)
    await state.update_data(age=age)

    await message.reply("Введите уровень вашей активности (минуты в день):")
    await state.set_state(ProfileForm.activity_level)  # Переход к следующему состоянию


# Обработчик ввода уровня активности
@router.message(ProfileForm.activity_level)
async def process_activity_level(message: Message, state: FSMContext):
    activity_level = message.text.strip()

    if not activity_level.isdigit():
        await message.reply("Пожалуйста, введите корректное число для уровня активности.")
        return

    activity_level = int(activity_level)
    await state.update_data(activity_level=activity_level)

    await message.reply("Введите ваш город:")
    await state.set_state(ProfileForm.city)  # Переход к следующему состоянию


# Обработчик ввода города

@router.message(ProfileForm.city)
async def process_city(message: Message, state: FSMContext):
    city = message.text.strip()
    await state.update_data(city=city)

    # Запрашиваем пол
    await message.reply("Введите ваш пол (М/Ж):")
    await state.set_state(ProfileForm.gender)  # Переход к следующему состоянию


@router.message(ProfileForm.gender)
async def process_gender(message: Message, state: FSMContext):
    gender = message.text.strip()

    if gender not in ["М", "Ж"]:
        await message.reply("Пожалуйста, введите корректный пол (М/Ж).")
        return

    await state.update_data(gender=gender)
    await message.reply(
        "Введите желаемое кол-во воды в сутки или ответьте 'рассчитай сам', чтобы рассчитать по формуле")
    await state.set_state(ProfileForm.water_goal)  # Переход к следующему состоянию


@router.message(ProfileForm.water_goal)
async def process_calorie_goal(message: Message, state: FSMContext):
    water = message.text.strip()
    if water == 'рассчитай сам':
        data = await state.get_data()
        user_id = message.from_user.id
        weight = data.get("weight")
        height = data.get("height")
        age = data.get("age")
        activity_level = data.get("activity_level")
        gender = data.get("gender")
        city = data.get("city")
        water_intake, _ = calculate_water_and_calories(weight, height, age, activity_level, gender)
    else:
        water_intake = int(water)
    await state.update_data(water_intake=water_intake)
    await message.reply(
        "Выберете тип питания {похудение, поддержка, набор} для автоматического расчета или введите сами норму каллорий")
    await state.set_state(ProfileForm.calorie_goal)  # Переход к следующему состоянию


# Обработчик ввода цели калорий
@router.message(ProfileForm.calorie_goal)
async def process_calorie_goal(message: Message, state: FSMContext):
    cal = message.text.strip()

    data = await state.get_data()
    user_id = message.from_user.id
    weight = data.get("weight")
    height = data.get("height")
    age = data.get("age")
    activity_level = data.get("activity_level")
    gender = data.get("gender")
    city = data.get("city")
    water_intake = data.get("water_intake")

    bias = 0
    if cal.isdigit():
        calorie_goal = int(cal)
    else:
        if cal == 'похудение':
            bias = -200
        if cal == 'набор':
            bias = 200
        _, calorie_goal = calculate_water_and_calories(weight, height, age, activity_level, gender)
    await state.update_data(calorie_goal=calorie_goal + bias)

    save_profile(user_id, weight, height, age, activity_level, city, gender, calorie_goal, water_intake)

    await message.reply(f"Ваш профиль обновлен:\n"
                        f"Вес: {weight} кг\n"
                        f"Рост: {height} см\n"
                        f"Возраст: {age} лет\n"
                        f"Уровень активности: {activity_level} минут в день\n"
                        f"Город: {city}\n"
                        f"Пол: {gender}\n"
                        f"Цель калорий: {calorie_goal}\n"
                        f"Цель воды:{water_intake}\n")

    await state.clear()


def calculate_water_and_calories(weight, height, age, activity_level, gender):
    # Расчёт нормы воды:
    # Базовая норма воды = вес × 30 мл/кг
    water_intake = weight * 30

    # Учитываем активность: +500 мл за каждые 30 минут активности
    water_intake += (activity_level // 30) * 500

    # Расчёт нормы калорий:
    # Базовый расчет (формула для мужчин):
    if gender == "М":
        calories = 10 * weight + 6.25 * height - 5 * age + 5
    else:  # Для женщин
        calories = 10 * weight + 6.25 * height - 5 * age - 161

    # Учитываем уровень активности:
    # Дополнительные калории в зависимости от уровня активности
    calories += 200 * (activity_level // 60)  # Например, +200 калорий за каждый час активности

    return water_intake, calories


# Функция для сохранения данных в базе данных
def save_profile(user_id, weight, height, age, activity_level, city, gender, calorie_goal, water_intake):
    conn = sqlite3.connect('user_profiles.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            weight REAL,
            height REAL,
            age INTEGER,
            activity_level INTEGER,
            city TEXT,
            gender TEXT,
            calorie_goal INTEGER, 
            water_intake REAL
        )
    ''')
    cursor.execute('''
        INSERT OR REPLACE INTO profiles (user_id, weight, height, age, activity_level, city,gender, calorie_goal, water_intake)
        VALUES (?,?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, weight, height, age, activity_level, city, gender, calorie_goal, water_intake))

    conn.commit()
    conn.close()


###############################################################################################################
def get_profile(user_id):
    conn = sqlite3.connect('user_profiles.db')
    cursor = conn.cursor()

    # Выполняем запрос для поиска пользователя по user_id
    cursor.execute('''
        SELECT * FROM profiles WHERE user_id = ?
    ''', (user_id,))

    # Извлекаем результат
    user_profile = cursor.fetchone()

    conn.close()

    return user_profile


def get_water(user_id):
    conn = sqlite3.connect('user_profiles.db')
    cursor = conn.cursor()
    date = datetime.now().strftime("%Y-%m-%d")  # Текущая дата и время
    # Выполняем запрос для поиска пользователя по user_id
    cursor.execute('''
        SELECT * FROM water WHERE user_id = ? and date = ?
    ''', (user_id, date))

    # Извлекаем результат
    user_profile = cursor.fetchone()

    conn.close()

    return user_profile


def update_or_create_user_water(user_id, water_amount):
    conn = sqlite3.connect('user_profiles.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS water (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            water_intake REAL DEFAULT 0,
            date TEXT NOT NULL DEFAULT CURRENT_DATE
        )
    ''')
    # Проверяем, существует ли уже лог воды для сегодняшней даты
    cursor.execute('''
        SELECT * FROM water WHERE user_id = ? AND date = CURRENT_DATE
    ''', (user_id,))

    user_profile = cursor.fetchone()

    if user_profile:
        _, user_id, current_water_intake, _ = user_profile
        # Если лог на сегодня уже существует, обновляем его
        cursor.execute('''
            UPDATE water SET water_intake = ? WHERE user_id = ? AND date = CURRENT_DATE
        ''', (current_water_intake + water_amount, user_id))
    else:
        # Если лога нет, создаем новый
        cursor.execute('''
            INSERT INTO water (user_id, water_intake) VALUES (?, ?)
        ''', (user_id, water_amount))

    conn.commit()
    conn.close()


@router.message(Command("profile"))
async def get_user_profile(message: Message):
    user_id = message.from_user.id  # Получаем user_id из сообщения

    # Получаем профиль пользователя
    profile = get_profile(user_id)

    if profile:
        # Если профиль найден, отправляем информацию
        __, _, weight, height, age, activity_level, city, gender, calorie_goal, water_intake = profile
        # water_intake, calories = calculate_water_and_calories(weight, height, age, activity_level, gender)

        await message.reply(f"Ваш профиль:\n"
                            f"Вес: {weight} кг\n"
                            f"Рост: {height} см\n"
                            f"Возраст: {age} лет\n"
                            f"Уровень активности: {activity_level} минут в день\n"
                            f"Город: {city}\n"
                            f"Пол: {gender}\n"
                            f"Цель калорий: {calorie_goal if calorie_goal else 'будет рассчитана автоматически'}\n"
                            f"\n"
                            f"**Дневная норма воды: {water_intake} мл**\n"
                            f"**Дневная норма калорий: {calorie_goal} ккал**"
                            )
    else:
        # Если профиль не найден, уведомляем пользователя
        await message.reply("У вас нет профиля. Используйте команду /set_profile для создания профиля.")


def update_water_intake(user_id, water_intake):
    conn = sqlite3.connect('user_profiles.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS water (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            water_intake REAL DEFAULT 0,
            date TEXT NOT NULL DEFAULT CURRENT_DATE
        )
    ''')

    # Обновляем количество воды для пользователя
    cursor.execute('''
        UPDATE water
        SET water_intake = ?
        WHERE user_id = ?''', (water_intake, user_id))

    conn.commit()
    conn.close()


@router.message(Command("log_water"))
async def log_water(message: Message):
    # Получаем количество воды, введенное пользователем
    try:
        water_amount = float(message.text.split()[1])
    except (IndexError, ValueError):
        await message.reply("Пожалуйста, введите количество воды, например: /log_water 500")
        return

    # Получаем профиль пользователя
    user_id = message.from_user.id
    update_or_create_user_water(user_id, water_amount)
    water = get_water(user_id)
    profile = get_profile(user_id)

    if profile is None:
        await message.reply("Профиль не найден.")
        return

    # Декомпозиция профиля
    _, user_id, weight, height, age, activity_level, city, gender, calorie_goal, water_intake = profile
    _, user_id, current_water_intake, date = water

    # Обновляем количество выпитой воды
    new_water_intake = current_water_intake
    update_water_intake(user_id, new_water_intake)

    # Вычисляем, сколько воды осталось до выполнения нормы
    remaining_water = water_intake - new_water_intake

    if remaining_water > 0:
        await message.reply(
            f"Вы выпили {water_amount} мл воды. Осталось выпить {remaining_water:.2f} мл до выполнения нормы.")
    else:
        await message.reply(f"Вы выпили {water_amount} мл воды. Норма выполнена! Молодец!")


# Словарь для хранения данных о продукте (будет использоваться временно, можно заменить на базу данных)
food_data = {}


def create_db_food():
    conn = sqlite3.connect("user_profiles.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS food_log (
                        user_id INTEGER,
                        date TEXT,
                        product TEXT,
                        weight REAL,
                        calories REAL
                      )''')
    conn.commit()
    conn.close()


# Функция для записи данных в базу
def log_to_db_food(user_id, product, weight, calories):
    conn = sqlite3.connect("user_profiles.db")
    cursor = conn.cursor()
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Текущая дата и время
    cursor.execute("INSERT INTO food_log (user_id, date, product, weight, calories) VALUES (?, ?, ?, ?, ?)",
                   (user_id, date, product, weight, calories))
    conn.commit()
    conn.close()


@router.message(Command("get_food_log"))
async def get_daily_calories(message: Message):
    user_id = message.from_user.id
    date = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect("user_profiles.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT SUM(calories) FROM food_log 
        WHERE user_id = ? AND date LIKE ?
    """, (user_id, f"{date}%"))
    result = cursor.fetchone()
    conn.close()
    profile = get_profile(user_id)
    _, user_id, weight, height, age, activity_level, city, gender, calorie_goal, water_intake = profile

    await message.reply(
        f"Вы съели {result[0]}. Осталось съесть {calorie_goal - result[0]} калорий до выполнения нормы.")


@router.message(Command("log_food"))
async def log_food(message: Message):
    # Запрашиваем продукт и кол-во
    try:
        product = message.text.split()[1]
        weight = float(message.text.split()[2])
    except (IndexError, ValueError):
        await message.reply("Пожалуйста, введите продукт и вес, например: /log_food banan 500")
        return

    # Формируем URL для запроса к API Open Food Facts
    url = f"https://world.openfoodfacts.org/cgi/search.pl?action=process&search_terms={product}&json=true"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()

            # Извлекаем продукты из ответа
            products = data.get('products', [])

            if products:
                # Берем первый продукт из списка
                first_product = products[0]

                # Получаем калории на 100 г продукта
                calories = first_product.get('nutriments', {}).get('energy-kcal_100g', 0)
                product_name = first_product.get('product_name', 'Неизвестно')

                total_calories = (calories * weight) / 100

                # Отправляем сообщение с результатом
                user_id = message.from_user.id
                create_db_food()
                log_to_db_food(user_id, product, weight, total_calories)
                await message.reply(f"Записано: {total_calories:.2f} ккал для {product_name} ({weight} г).")

            else:
                await message.reply("Продукт не найден.")


# Функция для создания базы данных и таблицы для тренировок
def create_db_workout():
    try:
        conn = sqlite3.connect("user_profiles.db")
        cursor = conn.cursor()

        # Создаем таблицу для тренировок
        cursor.execute('''CREATE TABLE IF NOT EXISTS workout_log (
                            user_id INTEGER,
                            date TEXT,
                            workout_type TEXT,
                            duration INTEGER,
                            calories_burned REAL,
                            water_needed REAL
                          )''')

        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"Ошибка при создании базы данных: {e}")


# Функция для записи информации о тренировке в базу данных
def log_to_db_workout(user_id, workout_type, duration, calories_burned, water_needed):
    try:
        conn = sqlite3.connect("user_profiles.db")
        cursor = conn.cursor()
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Текущая дата и время
        cursor.execute(
            "INSERT INTO workout_log (user_id, date, workout_type, duration, calories_burned, water_needed) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, date, workout_type, duration, calories_burned, water_needed))
        conn.commit()
        conn.close()
        print(
            f"Запись о тренировке успешно добавлена: {user_id}, {workout_type}, {duration} мин, {calories_burned} ккал, {water_needed} мл воды")
    except sqlite3.Error as e:
        print(f"Ошибка при записи в базу данных: {e}")


# Функция для расчета сожженных калорий и необходимого количества воды в зависимости от типа тренировки
def calculate_workout_burn(workout_type, duration):
    workout_types = {
        "бег": 10,  # 10 ккал на минуту
        "плавание": 8,  # 8 ккал на минуту
        "тренажерный зал": 6,  # 6 ккал на минуту
        "велосипед": 7  # 7 ккал на минуту
    }

    # Проверка, существует ли такой тип тренировки
    if workout_type not in workout_types:
        return 0, 0, "Неизвестный тип тренировки"

    calories_per_minute = workout_types[workout_type]
    calories_burned = calories_per_minute * duration

    # Расчет воды
    water_needed = (duration // 30) * 200  # 200 мл воды за каждые 30 минут

    return calories_burned, water_needed, None


@router.message(Command("log_workout"))
async def log_workout(message: Message):
    try:
        workout_type, duration_str = message.text.split()[1], message.text.split()[2]
        duration = int(duration_str)
    except (IndexError, ValueError):
        await message.reply(
            "Пожалуйста, введите тип тренировки и продолжительность в минутах, например: /log_workout бег 30")
        return

    # Расчет калорий и воды
    calories_burned, water_needed, error = calculate_workout_burn(workout_type, duration)

    if error:
        await message.reply(error)
        return

    # Получаем id пользователя
    user_id = message.from_user.id

    # Создаем базу, если ее еще нет
    create_db_workout()

    # Записываем информацию о тренировке в базу
    log_to_db_workout(user_id, workout_type, duration, calories_burned, water_needed)

    # Ответ пользователю
    await message.reply(
        f"🏃‍♂️ {workout_type.capitalize()} {duration} минут — {calories_burned} ккал. Дополнительно: выпейте {water_needed} мл воды.")


# Команда для отображения прогресса
@router.message(Command("check_progress"))
async def check_progress(message: Message):
    # Получаем ID пользователя
    await get_daily_calories(message)

    user_id = message.from_user.id
    _, user_id, weight, height, age, activity_level, city, gender, calorie_goal, water_intake = get_profile(user_id)
    _, user_id, current_water_intake, date = get_water(user_id)  # сколько выпили
    await message.reply(
        f"Вы выпили {current_water_intake} мл воды. Осталось выпить {water_intake - current_water_intake} мл до выполнения нормы.")


def get_water_data(user_id):
    conn = sqlite3.connect("user_profiles.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT date, water_intake FROM water 
        WHERE user_id = ? ORDER BY date
    """, (user_id,))
    data = cursor.fetchall()
    conn.close()
    return data


# Функция для получения данных о потребленных калориях
def get_food_data(user_id):
    conn = sqlite3.connect("user_profiles.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT date, SUM(calories) FROM food_log 
        WHERE user_id = ? GROUP BY date ORDER BY date
    """, (user_id,))
    data = cursor.fetchall()
    conn.close()
    return data


def create_progress_graph(user_id):
    water_data = get_water_data(user_id)
    food_data = get_food_data(user_id)

    water_dates = [x[0] for x in water_data]
    water_values = [x[1] for x in water_data]

    food_dates = [x[0] for x in food_data]
    food_values = [x[1] for x in food_data]

    target_water = 2400  # Примерная цель по воде (в мл)
    target_calories = 2500  # Примерная цель по калориям (в ккал)

    fig, ax1 = plt.subplots()

    ax1.set_xlabel('Дата')
    ax1.set_ylabel('Вода (мл)', color='blue')
    ax1.plot(water_dates, water_values, color='blue', label='Вода', marker='o')

    ax1.axhline(y=target_water, color='blue', linestyle='--', label="Цель по воде")  # Линия цели по воде

    ax2 = ax1.twinx()
    ax2.set_ylabel('Калории (ккал)', color='red')
    ax2.plot(food_dates, food_values, color='red', label='Калории', marker='s')

    ax2.axhline(y=target_calories, color='red', linestyle='--', label="Цель по калориям")  # Линия цели по калориям

    ax1.tick_params(axis='y', labelcolor='blue')
    ax2.tick_params(axis='y', labelcolor='red')
    ax1.tick_params(axis='x', rotation=45)

    ax1.legend(loc='upper left')
    ax2.legend(loc='upper right')

    file_path = "progress_graph.png"
    fig.savefig(file_path)
    # Сохраняем график в BytesIO
    buf = BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)  # Возвращаем указатель в начало буфера
    return buf  # Возвращаем буфер


# Команда для отправки прогресса
@router.message(Command("show_progress"))
async def show_progress(message: Message):
    user_id = message.from_user.id

    # Генерируем график и получаем буфер с графиком
    graph_buf = create_progress_graph(user_id)
    await message.send_photo(chat_id=message.chat.id, photo=graph_buf)


# Функция для подключения обработчиков
def setup_handlers(dp):
    dp.include_router(router)
