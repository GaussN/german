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
            cur = conn.execute("SELECT * FROM networks WHERE uuid = ? and password = ?", (str(_uuid), _password, ))
            cur.row_factory = sqlite3.Row
            _res = cur.fetchone()
            ic(_res)
            _res = _res and models.Network(**_res) or None  # boolshit
            return _res

    @staticmethod
    def get() -> list[models.Network]:
        with sqlite3.connect(DB_CONN_STRING) as conn:
            cur = conn.execute("SELECT * FROM networks")
            cur.row_factory = sqlite3.Row
            return [models.Network(**_) for _ in cur.fetchall()]


    @staticmethod
    def get_by_container_id(container_id: str) -> models.Network:
        with sqlite3.connect(DB_CONN_STRING) as conn:
            cur = conn.execute("SELECT * FROM networks WHERE container_id = ?", (container_id,))
            cur.row_factory = sqlite3.Row
            network_dict = cur.fetchone()
            if not network_dict:
                return None
            network = ic(models.Network(**network_dict))
            cur.close()
            return network

    @staticmethod
    def delete(_uuid: uuid.UUID) -> None:
        with sqlite3.connect(DB_CONN_STRING) as conn:
            conn.execute("DELETE FROM networks WHERE uuid = ?", (str(_uuid),))


    @staticmethod
    def get_statistic() -> dict:
        statistics: list[models.Statistic] = list()
        with sqlite3.connect(DB_CONN_STRING) as conn:
            query = "SELECT * FROM stats" 
            cur = conn.execute(query)
            cur.row_factory = sqlite3.Row
            return cur.fetchall()


if __name__ == '__main__':
    with sqlite3.connect(DB_CONN_STRING) as conn:
        conn.execute(
            """
                CREATE TABLE networks(
                    uuid TEXT PRIMARY KEY,
                    container_id TEXT UNIQUE,
                    name TEXT UNIQUE,
                    password TEXT, 
                    peers INTEGER,
                    host TEXT
                );
            """)

        conn.execute(
                """
                CREATE TABLE stats(
                    id integer primary key autoincrement,
                    host text,
                    uuid text unique,
                    timestamp integer
                );
                """)

        conn.execute(
                """
                CREATE TRIGGER stats_trigger 
                after insert on networks 
                for each row 
                begin 
                    insert into stats(host, uuid, timestamp) values(NEW.host, NEW.uuid, strftime('%s', 'now'));
                end;
                """)
        
