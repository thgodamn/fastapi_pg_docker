from typing import List

import databases
import sqlalchemy
from fastapi import FastAPI
from fastapi import Request
from pydantic import BaseModel
import urllib.request
import json
import datetime

DATABASE_URL = "postgresql://postgres_user:1235@db/db_questions"

database = databases.Database(DATABASE_URL)

metadata = sqlalchemy.MetaData()

questions = sqlalchemy.Table(
    "questions",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("question", sqlalchemy.String),
    sqlalchemy.Column("answer", sqlalchemy.String),
    sqlalchemy.Column("create_at", sqlalchemy.DateTime()),
)


engine = sqlalchemy.create_engine(
    DATABASE_URL
)
metadata.create_all(engine)
conn = engine.connect()

class Question(BaseModel):
    id: int
    question: str
    answer: str

previous_question = [-1,-1]
app = FastAPI()


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.get("/q/", response_model=List[Question])
async def show_questions():
    query = questions.select()
    return await database.fetch_all(query)

@app.post("/q/")
async def get_questions(req: Request):
    req_info = await req.json()

    global previous_question
    check_new_question = False
    check_json_data_completed = False
    current_count = req_info['questions_num']

    while check_new_question == False:

        if check_json_data_completed == True:
            current_count = 1
        url = "https://jservice.io/api/random?count={}".format(current_count)
        data = urllib.request.urlopen(url).read()
        json_data = json.loads(data)

        for json_question in json_data:
            previous_question[0] = previous_question[1]
            query = questions.select().where(questions.c.id == json_question['id'])
            result = await database.fetch_all(query)
            if not result:
                previous_question[1] = json_question['id']
                check_new_question = True
                print(json_question['id'])
                print(json_question['question'])
                print(json_question['answer'])
                insert_query = questions.insert().values(id=json_question['id'], question=json_question['question'], answer=json_question['answer'], create_at=datetime.datetime.now())
                await database.execute(insert_query)

            check_json_data_completed = True

    if previous_question[0] == -1:
        return []
    else:
        query = questions.select().where(questions.c.id == previous_question[0])
        result = await database.fetch_all(query)
        return result
    #pass