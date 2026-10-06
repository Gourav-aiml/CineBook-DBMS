"""
CineBook Database Connector Module
Provides MySQL connection pooling, transactional context management,
and parameterized query execution with dictionary cursors.
"""

import os
import logging
from contextlib import contextmanager
import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Connection configuration from environment
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "cinebook")
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", 10))

_connection_pool = None


def get_pool():
    """Initializes and returns the MySQL connection pool."""
    global _connection_pool
    if _connection_pool is None:
        try:
            _connection_pool = pooling.MySQLConnectionPool(
                pool_name="cinebook_pool",
                pool_size=DB_POOL_SIZE,
                pool_reset_session=True,
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                autocommit=False,  # Transactions are managed explicitly
            )
            logger.info("MySQL connection pool 'cinebook_pool' established successfully.")
        except mysql.connector.Error as err:
            logger.error(f"Failed to create MySQL connection pool: {err}")
            raise
    return _connection_pool


def get_connection():
    """Fetches a connection from the pool, or creates a standalone one if pool is unavailable."""
    try:
        pool = get_pool()
        return pool.get_connection()
    except Exception as e:
        logger.warning(f"Connection pool acquisition failed, falling back to direct connection: {e}")
        return mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            autocommit=False,
        )


@contextmanager
def db_transaction():
    """
    Context manager for atomic database transactions.
    Ensures explicit BEGIN, COMMIT on success, and ROLLBACK on error.
    """
    conn = get_connection()
    try:
        conn.autocommit = False
        conn.start_transaction()
        yield conn
        conn.commit()
    except Exception as err:
        conn.rollback()
        logger.error(f"Transaction rolled back due to error: {err}")
        raise
    finally:
        conn.close()


def query_all(query, params=None):
    """Executes a read query and returns all rows as a list of dicts."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        return cursor.fetchall()
    except mysql.connector.Error as err:
        logger.error(f"query_all error: {err} | Query: {query}")
        raise
    finally:
        cursor.close()
        conn.close()


def query_one(query, params=None):
    """Executes a read query and returns a single row as a dict."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        return cursor.fetchone()
    except mysql.connector.Error as err:
        logger.error(f"query_one error: {err} | Query: {query}")
        raise
    finally:
        cursor.close()
        conn.close()


def execute_query(query, params=None, autocommit=True):
    """Executes an INSERT/UPDATE/DELETE query with parameters."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params or ())
        if autocommit:
            conn.commit()
        last_id = cursor.lastrowid
        row_count = cursor.rowcount
        return last_id if last_id else row_count
    except mysql.connector.Error as err:
        if autocommit:
            conn.rollback()
        logger.error(f"execute_query error: {err} | Query: {query}")
        raise
    finally:
        cursor.close()
        conn.close()
