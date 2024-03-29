import datetime
import io
from typing import Annotated
from fastapi import FastAPI, Header, Request
from fastapi.responses import RedirectResponse, StreamingResponse
from starlette import status
from pymongo import MongoClient
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_USR=os.getenv("MONGO_USR")
MONGO_PWD=os.getenv("MONGO_PWD")
MONGO_HOST=os.getenv("MONGO_HOST")
MONGO_APP_NAME=os.getenv("MONGO_APP_NAME")

MONGO_URI = f"mongodb+srv://{MONGO_USR}:{MONGO_PWD}@{MONGO_HOST}/?retryWrites=true&w=majority&appName={MONGO_APP_NAME}"

app = FastAPI()


def get_collection(database: str, collection: str):
    client = MongoClient(MONGO_URI)
    db = client[database]
    return db[collection]

def get_data(project: str=""):
    records = get_collection("redirect", "records")
    data = []
    if project != "":
        cursor = records.find({"project": project}, {"_id": 0, "timestamp": 1, "ip_address": 1, "url": 1})
        data = [
            {
                "timestamp": record["timestamp"],
                "ip_address": record["ip_address"],
                "url": record["url"],
            }
            for record in cursor
        ]
    return data


@app.get("/mongo")
async def mongo(project: str=""):
    return get_data(project)


@app.get("/csv", response_class=StreamingResponse)
async def csv():
    df = pd.DataFrame(get_data())
    stream = io.StringIO()
    df.to_csv(stream, index=False)
    response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=data.csv"
    return response

@app.get("/ping")
def ping():
    return {"ping": "pong"}

@app.get("/")
async def index(request: Request, project:str="", url: str = ""):
    current_time = datetime.datetime.now()
    ip_address = request.client.host
    user_agent = request.headers.get("user-agent", "unknown")
    record = {
        "url": url,
        "project": project,
        "timestamp": current_time,
        "user_agent": user_agent,
        "ip_address": ip_address,
    }
    records = get_collection("redirect", "records")
    records.insert_one(record)
    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)
