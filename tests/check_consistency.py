import sqlite3
from importlib import import_module
from dotenv import load_dotenv
import os
import psycopg2
import psycopg
from psycopg import ClientCursor, connection as _connection
from psycopg.rows import dict_row
from psycopg2 import extras
from dataclasses import dataclass, field, fields
import sys
import uuid
from datetime import datetime
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
load_data_path = os.path.join(parent_dir, "sqlite_to_postgres")
sys.path.append(load_data_path)

from load_data import Movie, Person, Genre, PersonMovie, GenreMovie, conn_context

def load_data(cursor, dataclass_type, table_name):
    cursor.execute(f"SELECT * FROM {table_name}")
    data = cursor.fetchall()
    return [
        dataclass_type(**convert_to_datetime(row))
        for row in data
    ]

def convert_to_datetime(row):
    row_dict = dict(row)
    for field_name, value in row_dict.items():
        if isinstance(value, str) and value.endswith('+00'):
            try:
                try:
                    # Correct usage of strptime:
                    row_dict[field_name] = datetime.strptime(value[:-3], '%Y-%m-%d %H:%M:%S.%f')
                except ValueError:
                    row_dict[field_name] = datetime.strptime(value[:-3], '%Y-%m-%d')
            except ValueError as e:
                print(f"Error converting '{value}' to datetime: {e}")
                # Consider a more robust error handling strategy here (log, skip, etc.)
        elif isinstance(value, uuid.UUID):
            row_dict[field_name] = str(value)
    return row_dict


def compare_tables(sqlite_conn, pg_conn, sqlite_table_name, pg_table_name, dataclass_type, log_file):
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()
    pg_cursor.rowfactory = psycopg2.extras.RealDictCursor
    try:
        sqlite_data = load_data(sqlite_cursor, dataclass_type, sqlite_table_name)
        pg_data = load_data(pg_cursor, dataclass_type, pg_table_name)

        sqlite_data.sort(key=lambda x: x.id)
        pg_data.sort(key=lambda x: x.id)

        assert len(sqlite_data) == len(pg_data), f"Table '{sqlite_table_name}' has different row counts"

        mismatches = []
        for i in range(len(sqlite_data)):
            if sqlite_data[i] != pg_data[i]:
                mismatches.append((sqlite_data[i], pg_data[i]))

        if mismatches:
            with open(log_file, 'a') as f:
                f.write(f"Mismatch in table '{sqlite_table_name}':\n")
                for sqlite_row, pg_row in mismatches:
                    f.write(f"SQLite: {sqlite_row}\nPostgreSQL: {pg_row}\n\n")
            return False

        return True

    except AssertionError as e:
        with open(log_file, 'a') as f:
            f.write(f"Error comparing {sqlite_table_name}: {e}\n")
        return False
    except Exception as e:
        with open(log_file, 'a') as f:
            f.write(f"Error comparing {sqlite_table_name}: {e}\n")
        return False
    finally:
        sqlite_cursor.close()
        pg_cursor.close()


if __name__ == "__main__":
    load_dotenv()

    dsl = {
        'dbname': os.getenv('POSTGRES_DB'),
        'user': os.getenv('POSTGRES_USER'),
        'password': os.getenv('POSTGRES_PASSWORD'),
        'host': os.getenv('POSTGRES_HOST'),
        'port': os.getenv('POSTGRES_PORT'),
    }

    db_path = '../sqlite_to_postgres/db.sqlite'
    tables_to_compare = [
        ("film_work", "content.film_work", Movie),
        ("genre", "content.genre", Genre),
        ("person", "content.person", Person),
        ("person_film_work", "content.person_film_work", PersonMovie),
        ("genre_film_work", "content.genre_film_work", GenreMovie),
    ]
    log_file = "comparison_log.txt"
    with open(log_file, 'w') as f:
        f.write("")

    with conn_context(db_path) as sqlite_conn, psycopg.connect(**dsl, row_factory=dict_row, cursor_factory=ClientCursor) as pg_conn:
        all_tables_match = True
        for sqlite_table, pg_table, dataclass in tables_to_compare:
            if not compare_tables(sqlite_conn, pg_conn, sqlite_table, pg_table, dataclass, log_file):
                all_tables_match = False

        if all_tables_match:
            print("All tables match!")
        else:
            print("Data mismatch detected!")

        pg_conn.close()