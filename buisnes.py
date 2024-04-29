"""
TODO: insert network in db table
TODO: grab peers keys to network_full object
"""
import os
import uuid
import socket

import docker
from icecream import ic

import db
import models

_DOCKER = docker.from_env()


def _get_free_port() -> int:
    _sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        _sock.bind(('', 0))            # os set free port
        return _sock.getsockname()[1]  # getsockname return tuple of address{0} and port{1}
    finally:
        _sock.close()


def _get_peers_keys() -> list[models.Keys]:
    return []


class Network:
    _CONFIGS_DIR = os.path.join(os.getcwd(), 'configs')

    @staticmethod
    def _create_container(_uuid: uuid.UUID, port: int, peers: int):
        _config_path = os.path.join(Network._CONFIGS_DIR, str(_uuid))
        ic(_config_path)
        _model = _DOCKER.containers. run(
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
    def create(network: models.NetworkCreate):
        _uuid = uuid.uuid4()
        os.mkdir(f'{Network._CONFIGS_DIR}/{_uuid}')
        ic(f'mkdir {_uuid}')

        _container = Network._create_container(_uuid, _get_free_port(), network.peers)
        ic(_container)

        network_full = models.Network(
            uuid=_uuid,
            container_id=_container.short_id,
            name=network.name,
            password=network.password,
            peers=network.peers,
            peers_keys=_get_peers_keys()
        )
        ic(network_full)

        # sb.Network.create(network_full)

        return network_full
