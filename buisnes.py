import ipaddress
import os
import pickle
import shutil
import sqlite3
import uuid
from re import compile
from uuid import uuid4, UUID
from ipaddress import IPv4Address
from sqlite3 import IntegrityError
from socket import socket, AF_INET, SOCK_STREAM
from contextlib import suppress

import docker
import docker.errors
from icecream import ic

import db
import models


_DOCKER = docker.from_env()

_REPLACE_PORT_TEMPLATE = compile(r':51820')


def _get_free_port() -> int:
    _sock = socket(AF_INET, SOCK_STREAM)
    try:
        _sock.bind(('', 0))  # os set free port
        return _sock.getsockname()[1]  # getsockname return tuple of address{0} and port{1}
    finally:
        _sock.close()


class DNS_record:
    def __init__(self, ip: str | IPv4Address, n: int):
        if isinstance(ip, str):
            ip = IPv4Address(ip)
        self.ip = ip
        self.n = n

    @staticmethod
    def get_default(n=None):
        return DNS_record('0.0.0.1', n or 0)


class DNS:
    def _set_peers_count_from_files(self):
        _filter = compile(r'peer\d{1,2}')
        _, _dirs, _ = next(os.walk(self._path))
        self._peers = len(list(filter(_filter.match, ic(_dirs))))
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
            for _record in self.dns_records:
                pickle.dump(_record, _dns_file)

    def _read_config(self, _n: int) -> str:
        if _n < 2 or _n > self._peers:
            raise ValueError('Invalid peer number')
        with open(os.path.join(self._path, f'peer{_n}', f'peer{_n}.conf')) as _config:
            return _config.read()

    def get_config(self, _ip: IPv4Address) -> str | None:
        self.load_records()
        try:
            for _record in self.dns_records:
                if _record.ip == IPv4Address('0.0.0.1'):
                    _record.ip = _ip
                    ic([_.__dict__ for _ in self.dns_records])
                    return self._read_config(_record.n)
            return None
        finally:
            self.dump_records()
            ic(f'dump records {self._path}')

    def _check_private_key(self, _private_key: str) -> int:
        ic(_private_key)
        for _n in range(2, self._peers + 1):
            with open(os.path.join(self._path, f'peer{_n}', f'privatekey-peer{_n}')) as _config:
                _key = ic(_config.read().strip())
                ic(_key == _private_key)
                if _key == _private_key:
                    return _n
        return 0

    def release_config(self, _ip: IPv4Address, _private_key: str) -> bool:
        _n = ic(self._check_private_key(_private_key))
        if not _n:
            return False
        self.load_records()
        try:
            for _record in self.dns_records:
                if _record.n == _n and _record.ip == _ip:
                    _record.ip = IPv4Address('0.0.0.1')
                    ic([_.__dict__ for _ in self.dns_records])
                    return True
            return False
        finally:
            self.dump_records()
            ic('dump records')


class Network:
    _CONFIGS_DIR = os.path.join(os.getcwd(), 'configs')

    @staticmethod
    def _create_container(_uuid: UUID, port: int, peers: int):
        _config_path = os.path.join(Network._CONFIGS_DIR, str(_uuid))
        ic(_config_path)
        _container = _DOCKER.containers.run(
            image=_DOCKER.images.get('lscr.io/linuxserver/wireguard'),
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
            ports={'51820/udp': port},
            volumes=[
                '/lib/modules:/lib/modules',
                f'{_config_path}:/config',
            ],
            sysctls={'net.ipv4.conf.all.src_valid_mark': 1},
        )
        return _container

    @staticmethod
    def create(network: models.NetworkCreate, host: str) -> models.Network:
        _uuid = uuid4()

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

        try:
            db.Network.create(ic(network_full))
        except IntegrityError as e:
            ic(e)
            Network.clear(network_full)
            return None

        return network_full

    @staticmethod
    def clear(network: models.Network) -> None:
        ic(f'clear {network.uuid}')
        with suppress(docker.errors.NotFound):
            _ = _DOCKER.containers.get(network.container_id)
            _.kill()
            ic('kill the containers')
        with suppress(FileNotFoundError):
            _ = os.path.join(Network._CONFIGS_DIR, str(network.uuid))
            shutil.rmtree(_)
            ic('remove the folder')
        db.Network.delete(network.uuid)
        ic('delete from db')

    @staticmethod
    def delete(network: models.NetworkDelete) -> uuid.UUID | None:
        password = network.password
        network = db.Network.get_by_container_id(network.container_id)
        if not network:
            return None
        if not db.Network.check_password(network.uuid, password):
            return None
        Network.clear(network)
        return network.uuid

    @staticmethod
    def get_config(_uuid: UUID, _ip: IPv4Address, _password: str) -> str | None:
        network: models.Network = db.Network.check_password(_uuid, _password)
        if not network:
            return None
        container_port = ic(_DOCKER.containers.get(network.container_id).ports['51820/udp'][0]['HostPort'])
        ic(container_port)
        _dns = DNS(os.path.join(Network._CONFIGS_DIR, str(_uuid)))
        _config = _dns.get_config(_ip)
        if _config:
            return _REPLACE_PORT_TEMPLATE.sub(f':{container_port}', _config)
        return None

    @staticmethod
    def release_config(_uuid: UUID, private_key: str, host: ipaddress.IPv4Network):
        _dns = DNS(os.path.join(Network._CONFIGS_DIR, str(_uuid)))
        return ic(_dns.release_config(_ip=host, _private_key=private_key))

    @staticmethod
    def get_networks() -> list[models.NetworkOut]:
        _networks = [models.NetworkOut(**_.__dict__) for _ in db.Network.get()]
        return ic(_networks)
