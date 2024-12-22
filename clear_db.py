import sqlite3
import os
from config.config import Config

def clear_database():
    try:
        # Проверяем существование файла БД
        if os.path.exists(Config.DATABASE):
            # Подключаемся к БД
            conn = sqlite3.connect(Config.DATABASE)
            cursor = conn.cursor()

            # Удаляем данные из всех таблиц
            cursor.execute('DELETE FROM chat_history')
            cursor.execute('DELETE FROM tokens')
            cursor.execute('DELETE FROM users')
            
            # Сбрасываем автоинкремент
            cursor.execute('DELETE FROM sqlite_sequence')
            
            # Сохраняем изменения
            conn.commit()
            conn.close()
            
            print("База данных успешно очищена")
        else:
            print("Файл базы данных не найден")
            
    except Exception as e:
        print(f"Ошибка при очистке базы данных: {str(e)}")

if __name__ == "__main__":
    clear_database() 