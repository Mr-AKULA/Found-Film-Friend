import sqlite3

def create_or_update_actions_table():
    """Создает или обновляет таблицу actions с нужной структурой"""
    conn = None
    try:
        conn = sqlite3.connect('movies.db')
        cursor = conn.cursor()

        # Проверяем существование таблицы
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='actions'")
        table_exists = cursor.fetchone()

        if table_exists:
            print("Таблица actions уже существует, проверяем структуру...")
            
            # Проверяем наличие всех нужных столбцов
            cursor.execute("PRAGMA table_info(actions)")
            columns = {col[1]: col for col in cursor.fetchall()}
            
            required_columns = {
                'action_id': {'type': 'INTEGER', 'pk': 1},
                'user_id': {'type': 'INTEGER', 'notnull': 1},
                'movie_id': {'type': 'INTEGER', 'notnull': 1},
                'want_to_watch': {'type': 'INTEGER'},
                'rating': {'type': 'INTEGER'},
                'timestamp': {'type': 'DATETIME', 'dflt_value': 'CURRENT_TIMESTAMP'}
            }
            
            # Проверяем каждый столбец
            needs_recreate = False
            for col_name, col_def in required_columns.items():
                if col_name not in columns:
                    print(f"Отсутствует столбец: {col_name}")
                    needs_recreate = True
                    break
                
                col_info = columns[col_name]
                if col_def.get('pk', 0) != col_info[5]:
                    print(f"Несоответствие PRIMARY KEY для столбца {col_name}")
                    needs_recreate = True
                    break
                
                if col_def.get('notnull', 0) != col_info[3]:
                    print(f"Несоответствие NOT NULL для столбца {col_name}")
                    needs_recreate = True
                    break
                
                if 'dflt_value' in col_def and col_info[4] != col_def['dflt_value']:
                    print(f"Несоответствие DEFAULT для столбца {col_name}")
                    needs_recreate = True
                    break
            
            if not needs_recreate:
                print("Таблица actions уже имеет правильную структуру")
                return True
                
            print("Необходимо пересоздать таблицу...")
            # Пересоздаем таблицу с правильной структурой
            cursor.execute("""
                CREATE TABLE actions_new (
                    action_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    movie_id INTEGER NOT NULL,
                    want_to_watch INTEGER,
                    rating INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE
                )
            """)
            
            # Переносим данные из старой таблицы
            cursor.execute("""
                INSERT INTO actions_new (action_id, user_id, movie_id, want_to_watch, rating)
                SELECT action_id, user_id, movie_id, want_to_watch, rating FROM actions
            """)
            
            cursor.execute("DROP TABLE actions")
            cursor.execute("ALTER TABLE actions_new RENAME TO actions")
            conn.commit()
            print("Таблица actions успешно обновлена")
            return True
            
        else:
            # Создаем новую таблицу
            cursor.execute("""
                CREATE TABLE actions (
                    action_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    movie_id INTEGER NOT NULL,
                    want_to_watch INTEGER,
                    rating INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE
                )
            """)
            conn.commit()
            print("Таблица actions успешно создана")
            return True
            
    except sqlite3.Error as e:
        print(f"Ошибка при работе с таблицей actions: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def verify_actions_table():
    """Проверяет корректность структуры таблицы actions"""
    conn = None
    try:
        conn = sqlite3.connect('movies.db')
        cursor = conn.cursor()

        # Проверяем существование таблицы
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='actions'")
        if not cursor.fetchone():
            print("Таблица actions не существует")
            return False

        # Проверяем наличие всех столбцов
        cursor.execute("PRAGMA table_info(actions)")
        columns = {col[1]: col for col in cursor.fetchall()}
        
        required_columns = ['action_id', 'user_id', 'movie_id', 'want_to_watch', 'rating', 'timestamp']
        
        for col in required_columns:
            if col not in columns:
                print(f"Отсутствует столбец: {col}")
                return False
        
        # Проверяем значение по умолчанию для timestamp
        timestamp_info = columns['timestamp']
        if timestamp_info[4] != 'CURRENT_TIMESTAMP':
            print("Столбец timestamp не имеет DEFAULT CURRENT_TIMESTAMP")
            return False
            
        print("Таблица actions имеет правильную структуру")
        return True
        
    except sqlite3.Error as e:
        print(f"Ошибка при проверке таблицы: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    if create_or_update_actions_table():
        print("Проверяем структуру таблицы...")
        verify_actions_table()
    else:
        print("Не удалось создать/обновить таблицу actions")