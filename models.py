import uuid

from icecream import ic
from pydantic import BaseModel


class Keys(BaseModel):
    private: str
    public: str


class Network(BaseModel):
    uuid: uuid.UUID
    container_id: str
    name: str
    password: str
    peers: int
    host: str
    # peers_keys: dict[int, Keys]

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


class NetworkOut(BaseModel):
    id: uuid.UUID
    name: str


class NetworkOut2Auth(NetworkOut):
    public: str


class NetworkDelete(BaseModel):
    id: uuid.UUID
    server_private_key: str
    holder_private_key: str
