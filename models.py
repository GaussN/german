import uuid

from icecream import ic
from pydantic import BaseModel


class Keys(BaseModel):
    peer_id: int
    private: str
    public: str


class Network(BaseModel):
    uuid: uuid.UUID
    container_id: str
    name: str
    password: str
    peers: int
    peers_keys: list[Keys]

    def dict(self, **kwargs):
        _ret_dict = super().dict(**kwargs)
        ic(_ret_dict)

        _p_keys: list[Keys] = _ret_dict["peers_keys"]
        _ret_dict["peers_keys"] = '\t'.join(f"{_k.peer_id}:{_k.get('private')}:{_k.get('public')}" for _k in _p_keys)

        ic(_ret_dict)
        return _ret_dict


class NetworkCreate(BaseModel):
    name: str
    password: str
    peers: int


class NetworkOut(BaseModel):
    id: uuid.UUID
    name: str


class NetworkOut2Auth(NetworkOut):
    public: str


class NetworkDelete(BaseModel):
    id: uuid.UUID
    server_private_key: str
    holder_private_key: str
