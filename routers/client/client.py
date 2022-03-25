from datetime import datetime
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi_jwt_auth import AuthJWT
from db.database import client_db

router = APIRouter(
    prefix="/client",
    tags=["client"],
    responses={404: {"description": "Not found"}},
)

client_db = client_db()


class client(BaseModel):
    android_version: str
    device_name: str
    sim_operator: str
    sim_country: str
    interval: str = 3000
    active: bool = True
    last_online: datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


async def update_lasttime(device_id: str):
    client_db.update(
        key=device_id,
        updates={"last_online": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
    )


@router.post("/add")
async def add_client(client: client):
    user = client_db.put(jsonable_encoder(client))
    return JSONResponse(
        {"success": True, "key": user["key"], "message": "client added successfully"}
    )


@router.get("/device/{key}")
async def get_client(key: str, Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    return JSONResponse({"success": True, "client": client_db.get(key)})


@router.get("/")
async def get_all_clients(Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    return JSONResponse(
        {
            "success": True,
            "clients": sorted(
                client_db.fetch().items,
                key=lambda i: datetime.fromisoformat(i["last_online"]),
                reverse=True,
            ),
        }
    )
