import uuid
import sqlite3

from icecream import ic

import models

DB_CONN_STRING = './.sqlite3'


class Network:
    @staticmethod
    def create(network: models.Network) -> models.Network:
        with sqlite3.connect(DB_CONN_STRING) as conn:
            cur = conn.execute(
                "INSERT INTO NETWORKS(uuid, container_id, name, password, peers, host)"
                "VALUES (:uuid, :container_id, :name, :password, :peers, :host)",
                network.dict()
            )
            _res = cur.fetchall()
            ic(_res)
            return network

    @staticmethod
    def check_password(_uuid: uuid.UUID, _password: str) -> models.Network | None:
        with sqlite3.connect(DB_CONN_STRING) as conn:
            cur = conn.execute("SELECT * FROM networks WHERE uuid = ? and password = ?", (_uuid, _password, ))
            cur.row_factory = sqlite3.Row
            _res = cur.fetchone()
            ic(_res)
            _res = _res and models.Network(**_res) or None  # boolshit
            return _res

    @staticmethod
    def get() -> list[models.Network]:
        with sqlite3.connect(DB_CONN_STRING) as conn:
            try:
                cur = conn.execute("SELECT * FROM networks")
                cur.row_factory = sqlite3.Row
                return [models.Network(**_) for _ in cur.fetchall()]
            finally:
                cur.close()

    @staticmethod
    def get_by_name() -> models.NetworkOut:
        raise NotImplemented

    @staticmethod
    def get_by_uuid() -> models.NetworkOut:
        raise NotImplemented

    @staticmethod
    def delete(_uuid: uuid.UUID) -> None:
        with sqlite3.connect(DB_CONN_STRING) as conn:
            cur = conn.execute("DELETE FROM networks WHERE uuid = ?", (str(_uuid),))
            ic(cur.fetchall())
            cur.close()


if __name__ == '__main__':
    with sqlite3.connect(DB_CONN_STRING) as conn:
        conn.execute(
            """
                CREATE TABLE IF NOT EXISTS networks(
                    uuid TEXT PRIMARY KEY,
                    container_id TEXT UNIQUE,
                    name TEXT UNIQUE,
                    password TEXT, 
                    peers INTEGER,
                    host TEXT
                )
            """)
