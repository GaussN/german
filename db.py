import uuid
import sqlite3

from icecream import ic

import models


DB_CONN_STRING = './.sqlite3'


class Network:
    @staticmethod
    def create(network: models.Network) -> models.Network:
        with sqlite3.connect(DB_CONN_STRING) as _conn:
            _cur = _conn.execute(
                "INSERT INTO NETWORKS(uuid, container_id, name, password, peers, peers_keys)"
                    "VALUES (:uuid, :container_id, :name, :password, :peers, :peers_keys)",
                network.dict()
            )
            _res = _cur.fetchall()
            ic(_res)
            return network

    @staticmethod
    def get():
        with sqlite3.connect(DB_CONN_STRING) as _conn:
            try:
                _cur = _conn.execute("SELECT * FROM networks")
                ic(_cur)
                return _cur.fetchall()
            finally:
                _cur.close()

    @staticmethod
    def get_by_name() -> models.NetworkOut:
        raise NotImplemented

    @staticmethod
    def get_by_uuid() -> models.NetworkOut:
        raise NotImplemented

    @staticmethod
    def delete(_uuid: uuid.UUID) -> None:
        with sqlite3.connect(DB_CONN_STRING) as _conn:
            _cur = _conn.execute("DELETE FROM networks WHERE uuid = ?", (str(_uuid),))
            ic(_cur.fetchall())
            _cur.close()


class User:
    @staticmethod
    def create():
        raise NotImplemented

    @staticmethod
    def delete():
        raise NotImplemented

    @staticmethod
    def get():
        raise NotImplemented


if __name__ == '__main__':
    with sqlite3.connect(DB_CONN_STRING) as _conn:
        _conn.execute(
            """
                CREATE TABLE IF NOT EXISTS networks(
                    uuid TEXT PRIMARY KEY,
                    container_id TEXT UNIQUE,
                    name TEXT UNIQUE,
                    password TEXT, 
                    peers INTEGER,
                    peers_keys TEXT
                )
            """)

        _conn.execute(
            """
                CREATE TABLE IF NOT EXISTS users(
                    id INTEGER,
                    network_uuid TEXT,
                    ip TEXT,
                    keys TEXT,
                    FOREIGN KEY(network_uuid) REFERENCES networks(uuid),
                    PRIMARY KEY (id, network_uuid)
                )
            """)
