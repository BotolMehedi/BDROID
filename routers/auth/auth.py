from fastapi import APIRouter, Depends
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from fastapi_jwt_auth import AuthJWT
from db.database import auth_db

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)

auth_db = auth_db()


class client(BaseModel):
    username: str
    password: str


class password(BaseModel):
    old_password: str
    new_password: str


def check_auth():
    data = auth_db.fetch().items
    if len(data) == 0:
        auth_db.put({"username": "botol", "password": "baba"})
    else:
        pass


@router.post("/login")
async def add_client(client: client, Authorize: AuthJWT = Depends()):
    user = auth_db.fetch(
        {"username": client.username, "password": client.password}
    ).items
    if len(user) == 0:
        raise HTTPException(status_code=401, detail="User not found")
    access_token = Authorize.create_access_token(subject=client.username,expires_time=False)
    return JSONResponse(
        {
            "success": True,
            "token": access_token,
            "message": "login successfully",
        }
    )


@router.post("/password/change")
async def get_client(password: password,Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    data = auth_db.fetch({"password": password.old_password}).items
    if len(data) == 0:
        raise HTTPException(status_code=401, detail="Incorrect old password")
    auth_db.update(key=data[0]["key"], updates={"password": password.new_password})
    return JSONResponse({"success": True, "message": "password changed successfully"})
