import uuid

from icecream import ic
from pydantic import BaseModel


class Keys(BaseModel):
    private: str
    public: str
    shared: str


class NetworkOut(BaseModel):
    uuid: uuid.UUID
    name: str


class Network(NetworkOut):
    container_id: str
    password: str
    peers: int
    host: str

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def dict(self, **kwargs):
        _ret_dict = super().dict(**kwargs)
        ic(_ret_dict)

        _uuid = _ret_dict["uuid"]
        _ret_dict["uuid"] = str(_uuid)

        ic(_ret_dict)
        return _ret_dict


class NetworkCreate(BaseModel):
    name: str
    password: str
    peers: int


class NetworkDeleteIn(BaseModel):
    name: str
    password: str
    container_id: str


class NetworkDelete(NetworkDeleteIn):
    host: str


class ReleaseConfigIn(BaseModel):
    private_key: str


class ReleaseConfig(ReleaseConfigIn):
    host: str
