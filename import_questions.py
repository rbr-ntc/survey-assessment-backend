#!/usr/bin/env python3
"""
Скрипт для импорта вопросов в MongoDB
Использование: python import_questions.py
"""

import json
import os
import sys

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

MONGO_URL = os.environ.get("MONGO_URL")
if not MONGO_URL:
    print("❌ Ошибка: MONGO_URL не установлен в переменных окружения")
    sys.exit(1)

QUESTIONS_FILE = "improved-test-questions.json"

async def import_questions():
    """Импортирует вопросы из JSON файла в MongoDB"""
    try:
        # Подключение к MongoDB
        print(f"🔌 Подключение к MongoDB...")
        client = AsyncIOMotorClient(MONGO_URL)
        db = client["assessment"]
        
        # Проверка подключения
        await client.admin.command('ping')
        print("✅ Подключение успешно")
        
        # Чтение файла с вопросами
        if not os.path.exists(QUESTIONS_FILE):
            print(f"❌ Ошибка: Файл {QUESTIONS_FILE} не найден")
            sys.exit(1)
        
        print(f"📖 Чтение файла {QUESTIONS_FILE}...")
        with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
            questions = json.load(f)
        
        if not isinstance(questions, list):
            print("❌ Ошибка: Файл должен содержать массив вопросов")
            sys.exit(1)
        
        print(f"📊 Найдено {len(questions)} вопросов")
        
        # Проверка существующих вопросов
        existing_count = await db.questions.count_documents({})
        if existing_count > 0:
            print(f"⚠️  В базе уже есть {existing_count} вопросов")
            response = input("Удалить существующие вопросы и импортировать заново? (y/n): ")
            if response.lower() == 'y':
                await db.questions.delete_many({})
                print("🗑️  Существующие вопросы удалены")
            else:
                print("❌ Импорт отменен")
                sys.exit(0)
        
        # Импорт вопросов
        print("📥 Импорт вопросов...")
        result = await db.questions.insert_many(questions)
        print(f"✅ Успешно импортировано {len(result.inserted_ids)} вопросов")
        
        # Проверка
        final_count = await db.questions.count_documents({})
        print(f"📊 Всего вопросов в базе: {final_count}")
        
        client.close()
        print("✅ Импорт завершен успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка при импорте: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import asyncio
    asyncio.run(import_questions())

