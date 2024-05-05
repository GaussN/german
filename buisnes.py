"""
TODO: переделать днс, хранить в файле массив или словарь с номерами пиров в виде ключей
"""
import os
import re
import uuid
import socket
import pickle
import ipaddress

import docker
from icecream import ic

import db
import models

_DOCKER = docker.from_env()


def _get_free_port() -> int:
    _sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        _sock.bind(('', 0))  # os set free port
        return _sock.getsockname()[1]  # getsockname return tuple of address{0} and port{1}
    finally:
        _sock.close()


class DNS_record:
    def __init__(self, ip: str | ipaddress.IPv4Address, n: int):
        if isinstance(ip, str):
            ip = ipaddress.IPv4Address(ip)
        self.ip = ip
        self.n = n

    @staticmethod
    def get_default(n=None):
        return DNS_record('0.0.0.1', n or 0)


class DNS:
    def _set_peers_count_from_files(self):
        _filter = re.compile(r'peer\d{1,2}')
        _, _dirs, _ = next(os.walk(self._path))
        ic(_dirs)
        self._peers = len(list(filter(_filter.match, _dirs)))
        ic(self._peers)

    def __init__(self, path: str):
        self._path = path
        self._peers = 0
        self._set_peers_count_from_files()
        self.dns_records: list[DNS_record] = []

        if not os.path.exists(os.path.join(path, 'dns')):
            ic('create dns file')
            self._gen_dns_file()
        self.load_records()
        ic('load dns data')

    def _gen_dns_file(self):
        # first peer reserved for host
        for peer in range(2, self._peers + 1):
            self.dns_records.append(DNS_record.get_default(peer))  # address by default
        self.dump_records()

    def load_records(self):
        _d = self.dns_records  # dump for exception case
        self.dns_records = []
        ic(_d, self.dns_records)
        try:
            with open(os.path.join(self._path, 'dns'), 'rb') as _dns_file:
                try:
                    while _dns_file:
                        self.dns_records.append(pickle.load(_dns_file))
                except EOFError:
                    pass
        except Exception as e:
            ic(e)
            self.dns_records = _d
            raise

    def dump_records(self):
        with open(os.path.join(self._path, 'dns'), 'wb') as _dns_file:
            _dns_file.seek(0)  # // pass
            for _record in self.dns_records:
                pickle.dump(_record, _dns_file)

    def _read_config(self, _n: int) -> str:
        if _n < 2 or _n > self._peers:
            raise ValueError('Invalid peer number')
        with open(os.path.join(self._path, f'peer{_n}', f'peer{_n}.conf')) as _config:
            return _config.read()

    def get_config(self, _ip: ipaddress.IPv4Address) -> str | None:
        self.load_records()
        try:
            for _record in self.dns_records:
                if _record.ip == ipaddress.IPv4Address('0.0.0.1'):
                    _record.ip = _ip
                    ic([_.__dict__ for _ in self.dns_records])
                    return self._read_config(_record.n)
            return None
        finally:
            self.dump_records()
            ic(f'dump records {self._path}')

    def release_config(self, _ip: ipaddress.IPv4Address) -> bool:
        self.load_records()
        try:
            for _record in self.dns_records:
                if _record.ip == _ip:
                    _record.ip = DNS_record.get_default(_record.n)
                    return True
            return False
        finally:
            self.dump_records()


class Network:
    _CONFIGS_DIR = os.path.join(os.getcwd(), 'configs')

    @staticmethod
    def _create_container(_uuid: uuid.UUID, port: int, peers: int):
        _config_path = os.path.join(Network._CONFIGS_DIR, str(_uuid))
        ic(_config_path)
        _model = _DOCKER.containers.run(
            image=_DOCKER.images.get('41af0e3f25a5'),
            detach=True,
            remove=True,
            name=str(_uuid),
            cap_add=["NET_ADMIN", "SYS_MODULE"],
            environment={
                'PUID': 1000,
                'PGID': 1000,
                'TZ': 'Etc/UTC',
                'SERVERPORT': 51820,
                'PEERS': peers,
                'PEERDNS': 'auto',
                'INTERNAL_SUBNET': '10.1.0.0',
                'ALLOWEDIPS': '0.0.0.0/0',
                'PERSISTENKEEPALIVE_PEERS': '',
                'LOG_CONFIG': True,
            },
            ports={'51280/udp': port},
            volumes=[
                '/lib/modules:/lib/modules',
                f'{_config_path}:/config',
            ],
            sysctls={'net.ipv4.conf.all.src_valid_mark': 1},
        )
        return _model

    @staticmethod
    def create(network: models.NetworkCreate, host: str):
        _uuid = uuid.uuid4()

        _config_dir = os.path.join(Network._CONFIGS_DIR, str(_uuid))
        os.mkdir(_config_dir)
        ic(f'mkdir {_uuid}')

        _container = Network._create_container(_uuid, _get_free_port(), network.peers)
        ic(_container)

        network_full = models.Network(
            uuid=_uuid,
            container_id=_container.short_id,
            name=network.name,
            password=network.password,
            peers=network.peers,
            host=host,
        )
        ic(network_full)

        try:
            db.Network.create(network_full)
        except Exception as e:
            ic(e)
            Network.clear(network_full)
            raise

        return network_full

    @staticmethod
    def clear(network: models.Network):
        ic(f'clear {network.uuid}')
        # kill the docker container
        _ = _DOCKER.containers.get(network.container_id)
        _.kill()
        ic('kill the containers')
        # remove configs dir
        _ = os.path.join(Network._CONFIGS_DIR, str(network.uuid))
        if os.path.exists(_):
            os.rmdir(_)
        ic('remove the folder')
        # delete record from db
        db.Network.delete(network.uuid)
        ic('delete from db')

    @staticmethod
    def delete(_uuid: uuid.UUID):
        """
        (1) SELECT * FROM `networks` WHERE `uuid` = :uuid LIMIT 1;
        (2) creating models.Network
        (3) invoke Network.clear(_)
        """
        raise NotImplementedError

    @staticmethod
    def get_config(_uuid: uuid.UUID, _ip: ipaddress.IPv4Address, _password: str):
        network: models.Network = db.Network.check_password(_uuid, _password)
        if not network:
            return None
        _dns = DNS(os.path.join(Network._CONFIGS_DIR, str(_uuid)))
        return _dns.get_config(_ip)

    @staticmethod
    def release_config(_uuid: uuid.UUID, _ip: ipaddress.IPv4Address):
        raise NotImplementedError
