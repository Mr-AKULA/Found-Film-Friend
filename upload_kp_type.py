"""
upload_kp_type.py
Читает тип фильма (movie/tv-series/cartoon/...) из movies.db
и заливает в колонку kp_type таблицы movies в Supabase.

Запуск: python upload_kp_type.py
"""

import sqlite3
import requests
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SUPABASE_URL     = 'https://swgvbagncvbkoyztrimz.supabase.co'
SERVICE_ROLE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN3Z3ZiYWduY3Zia295enRyaW16Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4MjQ2Njk5MSwiZXhwIjoyMDk4MDQyOTkxfQ.Ytqbmqpfzx16Fdu6p65qX9tMYoMlybWVf7Y-cJ2vqWA'
DB_PATH          = 'movies.db'
BATCH_SIZE       = 1000

HEADERS = {
    'apikey':        SERVICE_ROLE_KEY,
    'Authorization': f'Bearer {SERVICE_ROLE_KEY}',
    'Content-Type':  'application/json',
}


def update_batch(ids, kp_type):
    id_list = ','.join(map(str, ids))
    resp = requests.patch(
        f'{SUPABASE_URL}/rest/v1/movies',
        headers=HEADERS,
        params={'id': f'in.({id_list})'},
        json={'kp_type': kp_type},
    )
    return resp.status_code in (200, 204)


def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Группируем фильмы по типу
    c.execute('SELECT type, COUNT(*) FROM movies GROUP BY type ORDER BY COUNT(*) DESC')
    groups = c.fetchall()
    print('Типы в SQLite:')
    for t, cnt in groups:
        print(f'  {t}: {cnt}')
    print()

    for kp_type, total in groups:
        c.execute('SELECT id FROM movies WHERE type = ?', (kp_type,))
        ids = [r[0] for r in c.fetchall()]

        print(f'Заливаю "{kp_type}" ({len(ids)} шт.)...')
        errors = 0
        for i in range(0, len(ids), BATCH_SIZE):
            batch = ids[i:i + BATCH_SIZE]
            ok = update_batch(batch, kp_type)
            done = min(i + BATCH_SIZE, len(ids))
            if ok:
                print(f'  {done}/{len(ids)} OK')
            else:
                errors += 1
                print(f'  {done}/{len(ids)} ОШИБКА')

        if errors == 0:
            print(f'  -> "{kp_type}" залито успешно\n')
        else:
            print(f'  -> "{kp_type}" {errors} батча(ей) с ошибкой\n')

    conn.close()
    print('Готово!')


if __name__ == '__main__':
    main()
