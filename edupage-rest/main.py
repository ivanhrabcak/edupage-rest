from datetime import date, datetime
from io import BytesIO
from typing import Any
from cachetools.func import ttl_cache
import orjson

from .annotations import logged_in, returns_edupage_object
from .types import EdupageCredentials, Message, UsernameAndPassword
from .edupage import get_edupage

from fastapi import FastAPI, HTTPException, File
from fastapi.responses import JSONResponse

from edupage_api import EduStudentSkeleton
from edupage_api.exceptions import BadCredentialsException, MissingDataException

class ORJsonResponse(JSONResponse):
    media_type = "application/json"

    def render(self, content: Any):
        return orjson.dumps(content)

app = FastAPI(default_response_class=ORJsonResponse)

@app.post("/authenticate")
def authenticate(credentials: EdupageCredentials):
    edupage = get_edupage()
    
    try:
        edupage.login(credentials.username, credentials.password, credentials.subdomain)
    except BadCredentialsException:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {"response": "OK"}

@app.post("/authenticate-auto")
def authenticate_auto(credentials: UsernameAndPassword):
    edupage = get_edupage()

    try:
        edupage.login_auto(credentials.username, credentials.password)
    except BadCredentialsException:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {"response": "OK"}

@app.get("/timetable")
@logged_in
@returns_edupage_object
def get_timetable(date: date):
    edupage = get_edupage()

    if not edupage.is_logged_in:
        raise HTTPException(status_code=400, detail="You first have to log in")
    
    return edupage.get_timetable(date)

@app.get("/students")
@logged_in
@returns_edupage_object
def get_students():
    return get_edupage().get_all_students()

@app.get("/teachers")
@logged_in
@returns_edupage_object
def get_teachers():
    return get_edupage().get_teachers()

@app.post("/message")
def send_message(message: Message):
    edupage = get_edupage()

    students = edupage.get_all_students() + edupage.get_teachers()
    def find_person(id: int):
        person_list = list(
            filter(lambda x: x.person_id == id, students)
        )

        class FakeEduStudent(EduStudentSkeleton):
            def get_id(self):
                return f"Student-{self.person_id}"
        
        person = person_list[0] if len(person_list) != 0 else None
        
        if person is None:
            return None

        if isinstance(person, EduStudentSkeleton):
            person = FakeEduStudent(person.person_id, person.name_short, person.class_id)

        return person

    recipients = [find_person(r) for r in message.recipients]

    if None in recipients:
        raise HTTPException(status_code=400, detail="Some of the accout ids you provided are invalid.")

    edupage.send_message(recipients, message.body)

    return {"response": "Ok"}

@app.get("/lunches")
@logged_in
@returns_edupage_object
def get_lunches(date: date):
    return get_edupage().get_lunches(date)

@app.post("/timeline")
@logged_in
@returns_edupage_object
@ttl_cache(maxsize=20, ttl=100)
def get_timeline(items_per_page: int, page: int):
    timeline = get_edupage().get_notifications()

    output = []
    for i in range(page * items_per_page, page * items_per_page + items_per_page):
        output.append(timeline[i])
    
    return output

@app.post("cloud-upload")
@returns_edupage_object
@logged_in
def cloud_upload(file: bytes = File(default=None)):
    if file is None:
        raise HTTPException(status_code=400, detail="No file sent!")

    return get_edupage().cloud_upload(BytesIO(file))

@app.get("/grades")
@returns_edupage_object
@logged_in
def get_grades():
    return get_edupage().get_grades()

@app.get("/missing-teachers")
@logged_in
@returns_edupage_object
def get_missing_teachers(date: date):
    return get_edupage().get_missing_teachers(date)

@app.get("/timetable-changes")
@returns_edupage_object
@logged_in
def get_timetable_changes(date: date):
    return get_edupage().get_timetable_changes(date)

@app.get("/school-year")
@logged_in
def get_school_year():
    return get_edupage().get_school_year()

@app.get("/foreign-timetable")
@logged_in
@returns_edupage_object
def get_foreign_timetable(id: int, date: date):
    try:
        return get_edupage().get_foreign_timetable(id, date)
    except MissingDataException as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/next-ringing")
@logged_in
@returns_edupage_object
def get_next_ringing_time(datetime: datetime):
    return get_edupage().get_next_ringing_time(datetime)