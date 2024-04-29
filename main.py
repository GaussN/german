"""

"""
import fastapi as fapi

import models


app = fapi.FastAPI(debug=__debug__)


async def create_network(request: fapi.Request, network: models.NetworkCreate) -> fapi.Response:
    pass


async def delete_network(request: fapi.Request) -> fapi.Response:
    pass


async def get_networks(request: fapi.Request) -> fapi.Response:
    pass


async def login_in_network(request: fapi.Request) -> fapi.Response:
    pass
