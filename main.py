from uuid import UUID
from ipaddress import IPv4Address

import fastapi as fapi
from icecream import ic

import models
import buisnes

app = fapi.FastAPI(debug=__debug__)


@app.post('/network')
async def create_network(request: fapi.Request, network: models.NetworkCreate) -> models.Network:
    new_network = buisnes.Network.create(network, request.client.host)
    if not new_network:
        return fapi.Response(
            status_code=fapi.status.HTTP_409_CONFLICT,
            content='Network with the same name already exists')
    return new_network


@app.post('/login')
async def login_in_network(
        request: fapi.Request,
        uuid_: str = fapi.Body(alias='uuid'),
        password: str = fapi.Body(alias='password')
) -> fapi.Response:
    config = buisnes.Network.get_config(uuid_, IPv4Address(request.client.host), password)
    return fapi.Response(content=config or 'Invalid uuid or password', headers={'Content-type': 'plain/text'})


@app.post('/logout')
async def release_config(
        request: fapi.Request,
        uuid_: str = fapi.Body(alias='uuid'),
        private_key: str = fapi.Body()
):
    result = buisnes.Network.release_config(
        _uuid=UUID(uuid_),
        host=IPv4Address(request.client.host),
        private_key=private_key
    )
    return fapi.Response(status_code=fapi.status.HTTP_200_OK)


@app.delete('/network')
async def delete_network(request: fapi.Request, network: models.NetworkDeleteIn) -> fapi.Response:
    result = buisnes.Network.delete(models.NetworkDelete(**network.__dict__, host=request.client.host))
    if ic(result):
        return fapi.Response(content=dict(result))
    return fapi.Response(status_code=fapi.status.HTTP_404_NOT_FOUND)


@app.get('/networks')
async def get_networks() -> list[models.NetworkOut]:
    return buisnes.Network.get_networks()


@app.get('/statistics')
async def get_statistics():
    return buisnes.Network.get_statistic()
