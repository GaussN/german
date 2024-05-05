"""

"""
import uuid

import fastapi as fapi

import models
import buisnes

app = fapi.FastAPI(debug=__debug__)


@app.post('/network')
async def create_network(request: fapi.Request, network: models.NetworkCreate) -> models.Network:
    new_network = buisnes.Network.create(network, request.client.host)
    return new_network


@app.post('/login')
async def login_in_network(
        request: fapi.Request,
        uuid_: str = fapi.Body(alias='uuid'),
        password: str = fapi.Body(alias='password')
) -> fapi.Response:
    config = buisnes.Network.get_config(uuid_, request.client.host, password)
    return fapi.Response(content=config or 'Invalid uuid or password ')


async def delete_network(request: fapi.Request) -> fapi.Response:
    pass


async def get_networks(request: fapi.Request) -> fapi.Response:
    pass
