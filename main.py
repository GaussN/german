"""

"""
from ipaddress import IPv4Address

import fastapi as fapi

import models
import buisnes

app = fapi.FastAPI(debug=__debug__)


@app.post('/network')
async def create_network(request: fapi.Request, network: models.NetworkCreate) -> models.Network:
    # try except
    new_network = buisnes.Network.create(network, request.client.host)
    return new_network


@app.post('/login')
async def login_in_network(
        request: fapi.Request,
        uuid_: str = fapi.Body(alias='uuid'),
        password: str = fapi.Body(alias='password')
) -> fapi.Response:
    # TODO: proccess full dns case
    config = buisnes.Network.get_config(uuid_, IPv4Address(request.client.host), password)
    return fapi.Response(content=config or 'Invalid uuid or password', headers={'Content-type': 'plain/text'})


async def delete_network(request: fapi.Request, network: models.NetworkDeleteIn) -> fapi.Response:
    response = buisnes.Network.delete(models.NetworkDelete(**network.__dict__, host=request.client.host))
    return fapi.Response(content=response)


@app.get('/networks')
async def get_networks(request: fapi.Request) -> list[models.NetworkOut]:
    return buisnes.Network.get_networks()
