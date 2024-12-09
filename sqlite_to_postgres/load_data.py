import sqlite3
from datetime import datetime

import psycopg
from psycopg import ClientCursor, connection as _connection
from psycopg.rows import dict_row
from contextlib import contextmanager
from dotenv import load_dotenv
from dataclasses import dataclass, field, fields
import uuid
import os

BATCH_SIZE = 100

@contextmanager
def conn_context(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

@dataclass
class Movie:
    title: str
    description: str
    rating: float = field(default=0.0)
    file_path: str = field(default=None)
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    type: str = field(default=None)
    creation_date: str = field(default=None)
    created_at: datetime = field(default=None)
    updated_at: datetime = field(default=None)

@dataclass
class Person:
    full_name: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime = field(default=None)
    updated_at: datetime = field(default=None)

@dataclass
class Genre:
    name: str
    description: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime = field(default=None)
    updated_at: datetime = field(default=None)

@dataclass
class PersonMovie:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    film_work_id: uuid.UUID = field(default_factory=uuid.uuid4)
    person_id: uuid.UUID = field(default_factory=uuid.uuid4)
    role: str = field(default=None)
    created_at: datetime = field(default=None)

@dataclass
class GenreMovie:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    film_work_id: uuid.UUID = field(default_factory=uuid.uuid4)
    genre_id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime = field(default=None)

class SQLiteLoader:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def load_from_sqlite(self, table_name):
        cursor = self.connection.cursor()
        try:
            cursor.execute(f"SELECT * FROM {table_name};")
            list_of_dictionaries = []
            while True:
                chunk = cursor.fetchmany(BATCH_SIZE)
                if not chunk:
                    break
                list_of_dictionaries.extend([dict(row) for row in chunk])
            return list_of_dictionaries
        except sqlite3.Error as e:
            print(f"Ошибка SQLite: {e}")
            return []
        finally:
            cursor.close()

class PostgresSaver:
    def __init__(self, connection: _connection):
        self.connection = connection

    def save_all_data(self, data, dataclass_type, table_name):
        cursor = self.connection.cursor()
        try:
            column_names = [field.name for field in fields(dataclass_type)]
            column_names_str = ','.join(column_names)
            col_count = ','.join(['%s'] * len(column_names))
            query = f"INSERT INTO {table_name} ({column_names_str}) VALUES ({col_count}) ON CONFLICT (id) DO NOTHING"

            for i in range(0, len(data), BATCH_SIZE):
                chunk = data[i:i + BATCH_SIZE]
                objects_to_insert = []
                for item_data in chunk:
                    try:
                        obj = dataclass_type(**item_data)
                        objects_to_insert.append(tuple(getattr(obj, attr) for attr in column_names))
                    except (KeyError, TypeError) as e:
                        print(f"Ошибка при обработке данных: {e}, item_data = {item_data}")
                if objects_to_insert:
                    cursor.executemany(query, objects_to_insert)
                    self.connection.commit()

        except psycopg.Error as e:
            self.connection.rollback()
            print(f"Ошибка PostgreSQL: {e}")
        except Exception as e:
            print(f"Произошла неизвестная ошибка: {e}")
        finally:
            cursor.close()


def load_from_sqlite(connection: sqlite3.Connection, pg_conn: _connection):
    postgres_saver = PostgresSaver(pg_conn)
    sqlite_loader = SQLiteLoader(connection)
    cursor = pg_conn.cursor()
    try:
        pg_conn.commit()
        data = sqlite_loader.load_from_sqlite('film_work')
        postgres_saver.save_all_data(data, Movie, 'content.film_work')
        data = sqlite_loader.load_from_sqlite('person')
        postgres_saver.save_all_data(data, Person, 'content.person')
        data = sqlite_loader.load_from_sqlite('genre')
        postgres_saver.save_all_data(data, Genre, 'content.genre')
        data = sqlite_loader.load_from_sqlite('genre_film_work')
        postgres_saver.save_all_data(data, GenreMovie, 'content.genre_film_work')
        data = sqlite_loader.load_from_sqlite('person_film_work')
        postgres_saver.save_all_data(data, PersonMovie, 'content.person_film_work')
    except psycopg.Error as e:
        pg_conn.rollback()
        print(f"Ошибка PostgreSQL: {e}")
    finally:
        cursor.close()

if __name__ == '__main__':
    load_dotenv()

    dsl = {
        'dbname': os.getenv('POSTGRES_DB'),
        'user': os.getenv('POSTGRES_USER'),
        'password': os.getenv('POSTGRES_PASSWORD'),
        'host': os.getenv('POSTGRES_HOST'),
        'port': os.getenv('POSTGRES_PORT'),
    }

    db_path = 'db.sqlite'
    with conn_context(db_path) as sqlite_conn, psycopg.connect(**dsl, row_factory=dict_row, cursor_factory=ClientCursor) as pg_conn:
        load_from_sqlite(sqlite_conn, pg_conn)
        pg_conn.close()
