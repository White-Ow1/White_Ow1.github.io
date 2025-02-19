import asyncio
import os
from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from text import WELCOME_TEXT, QUESTIONS
import nest_asyncio

# Применение nest_asyncio для обеспечения совместимости асинхронных функций
nest_asyncio.apply()

# Токен Telegram-бота
TOKEN = "7838758888:AAEE2mts6xyulLH8J7IpGkHwjbP69-NY5WE"

# Инициализация бота, диспетчера и роутера
bot = Bot(token=TOKEN)  # Инициализируем объект бота с токеном
dp = Dispatcher()  # Создаем объект диспетчера для управления маршрутизацией
router = Router()  # Создаем роутер для представления команд и сообщений

# Создание клавиатуры для команды /start
def get_start_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Начать тест")]],  # Создаем кнопку "Начать тест"
        resize_keyboard=True  # Настраиваем размер клавиатуры
    )

# Хранилище ответов пользователей
user_answers = {}  # Словарь для хранения ответов пользователей по их ID

# Обработчик для команды /start
@router.message(Command("start"))
async def start_command(message: types.Message):
    """
    Обработчик команды /start. Сбрасывает предыдущие ответы пользователя
    и отправляет приветственное сообщение.
    """
    user_answers[message.from_user.id] = []  # Инициализируем список ответов для нового пользователя
    await message.answer(WELCOME_TEXT, reply_markup=get_start_keyboard())  # Отправляем приветственное сообщение с кнопками

# Обработчик для кнопки "Начать тест"
@router.message(lambda message: message.text == "Начать тест")
async def start_test(message: types.Message):
    """
    Обработчик начала теста. Отправляет первый вопрос.
    """
    await send_question(message.from_user.id, block=1, question=1)  # Отправляем первый вопрос

# Функция для отправки конкретного вопроса пользователю
async def send_question(user_id, block, question):
    """
    Функция для отправки конкретного вопроса пользователю.

    :param user_id: ID пользователя
    :param block: Номер текущего блока вопросов
    :param question: Номер текущего вопроса в блоке
    """
    question_data = QUESTIONS[block - 1][question - 1]  # Получаем данные текущего вопроса
    question_text = question_data['text']  # Извлекаем текст вопроса
    options = question_data['options']  # Получаем варианты ответов

    # Создание кнопок для ответа
    markup = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=option['text']) for option in options]],  # Создаем кнопки для каждого варианта ответа
        resize_keyboard=True,  # Настраиваем размер клавиатуры
        one_time_keyboard=True  # Клавиатура исчезает после нажатия
    )

    # Отправка текста вопроса и кнопок пользователю
    await bot.send_message(user_id, question_text, reply_markup=markup)

# Обработчик для всех текстовых сообщений
@router.message()
async def handle_answer(message: types.Message):
    """
    Обработчик ответов пользователя на вопросы.

    :param message: Сообщение от пользователя
    """
    user_id = message.from_user.id  # Получаем ID пользователя

    # Определение текущего блока и вопроса
    answers = user_answers.get(user_id, [])  # Получаем список ответов пользователя
    block = len(answers) // 3 + 1  # Определяем номер текущего блока (предполагая 3 вопроса на блок)
    question = len(answers) % 3 + 1  # Определяем номер текущего вопроса в блоке

    # Получаем данные текущего вопроса
    question_data = QUESTIONS[block - 1][question - 1]  # Извлекаем данные вопроса
    options = question_data['options']  # Получаем варианты ответов

    # Проверка, что ответ валиден
    for option in options:  # Проходим по всем вариантам ответа
        if message.text == option['text']:  # Если текст сообщения совпадает с текстом варианта ответа
            answers.append(option['code'])  # Добавляем код выбранного варианта в список ответов
            user_answers[user_id] = answers  # Обновляем хранилище ответов
            break
    else:
        await message.answer("Пожалуйста, выберите один из предложенных вариантов ответа.")  # Ответ на неправильный выбор
        return

    # Переход к следующему вопросу или завершение блока
    if question == 3:  # Если текущий вопрос последний в блоке
        if block == 4:  # Если завершен последний блок теста
            await finish_test(user_id)  # Завершаем тест
        else:
            await send_question(user_id, block + 1, 1)  # Переходим к первому вопросу следующего блока
    else:
        await send_question(user_id, block, question + 1)  # Переходим к следующему вопросу в пределах блока

# Завершение теста: подсчет результатов и отправка их пользователю
async def finish_test(user_id):
    """
    Завершение теста: подсчет результатов и отправка их пользователю.

    :param user_id: ID пользователя
    """
    answers = user_answers[user_id]  # Получаем ответы пользователя
    # Подсчет количества ответов по типам
    result = {
        'E': answers.count('E'), 'I': answers.count('I'),
        'S': answers.count('S'), 'N': answers.count('N'),
        'T': answers.count('T'), 'F': answers.count('F'),
        'J': answers.count('J'), 'P': answers.count('P'),
    }

    # Определение доминирующих типов
    result_text = (
            ('E' if result['E'] >= result['I'] else 'I') +  # Определяем, какой тип преобладает
            ('S' if result['S'] >= result['N'] else 'N') +
            ('T' if result['T'] >= result['F'] else 'F') +
            ('J' if result['J'] >= result['P'] else 'P')
    )  # Формируем строку результата типа

    # Убедимся, что папка results существует
    os.makedirs("results", exist_ok=True)  # Создаем папку results, если она не существует

    # Сохранение результатов в файл
    with open(f"results/results_{user_id}.txt", "w") as f:
        f.write(f"Answers: {answers}\nResult: {result_text}\n")  # Записываем ответы и результат в файл

    # Отправка результата пользователю
    await bot.send_message(user_id, f"Ваш результат: {result_text}")  # Сообщаем результат пользователю

# Основная функция для запуска бота
async def main():
    """
    Основная функция для запуска бота.
    """
    # Регистрация роутера
    dp.include_router(router)  # Подключаем роутер к диспетчеру

    # Запуск бота
    await bot.delete_webhook(drop_pending_updates=True)  # Удаляем вебхук, если он есть, и игнорируем ожидания
    await dp.start_polling(bot)  # Запускаем процесс прослушивания обновлений

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()  # Применяем async-среду
    asyncio.run(main())  # Запускаем основную функцию