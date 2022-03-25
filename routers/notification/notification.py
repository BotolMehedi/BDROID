from datetime import datetime
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi_jwt_auth import AuthJWT
from db.database import notification_db

router = APIRouter(
    prefix="/notification",
    tags=["notification"],
    responses={404: {"description": "Not found"}},
)

notification_db = notification_db()


class notification(BaseModel):
    id: str
    device_id: str
    Package: str
    titleText: str = "null"
    notificationBodyText: str = "null"
    date: datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@router.post("/add")
async def add_notification(notification: notification):
    response = jsonable_encoder(notification)
    del response["id"]
    del response["date"]
    data = notification_db.fetch(response).items
    if len(data) > 0:
        return JSONResponse({"success": False, "message": "notification already exists"})
    notification_db.put(jsonable_encoder(notification))
    return JSONResponse({"success": True, "message": "notification added successfully"})


@router.get("/device/{device_name}")
async def get_notification(device_name: str, Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    response = []
    data = notification_db.fetch({"device_id": device_name}).items
    for i in data:
        del i["key"]
        del i["id"]
        response.append(list(i.values()))
    return JSONResponse(
        {
            "success": True,
            "notification": response,
        }
    )


@router.get("/")
async def get_notifications(Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    response = []
    data = notification_db.fetch().items
    for i in data:
        del i["key"]
        del i["id"]
        response.append(list(i.values()))
    return JSONResponse(
        {
            "success": True,
            "notification": sorted(
                response, key=lambda i: datetime.fromisoformat(i[1]), reverse=True
            ),
        }
    )


@router.get("/delete/{id}")
async def delete_notification(id: str, Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    data = notification_db.fetch({"device_id": id}).items
    for i in data:
        notification_db.delete(i["key"])
    return JSONResponse(
        {"success": True, "message": "notification deleted successfully"}
    )
