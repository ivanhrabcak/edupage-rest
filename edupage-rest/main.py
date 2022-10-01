from datetime import date, datetime
from io import BytesIO
from typing import Any
from uuid import uuid4
from cachetools.func import ttl_cache
import orjson

from .annotations import authenticated, get_global_ttl_cache, logged_in, returns_edupage_object
from .types import EdupageCredentials, Message, UsernameAndPassword

from fastapi import FastAPI, HTTPException, File
from fastapi.responses import JSONResponse

from edupage_api import EduStudentSkeleton, Edupage
from edupage_api.exceptions import BadCredentialsException, MissingDataException

class ORJsonResponse(JSONResponse):
    media_type = "application/json"

    def render(self, content: Any):
        return orjson.dumps(content)

app = FastAPI(default_response_class=ORJsonResponse)

@app.post("/authenticate")
def authenticate(credentials: EdupageCredentials):
    edupage = Edupage()
    
    try:
        edupage.login(credentials.username, credentials.password, credentials.subdomain)
    except BadCredentialsException:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = str(uuid4())
    
    get_global_ttl_cache()[token] = edupage

    return {"response": token}

@app.post("/authenticate-auto")
def authenticate_auto(credentials: UsernameAndPassword):
    edupage = Edupage()

    try:
        edupage.login_auto(credentials.username, credentials.password)
    except BadCredentialsException:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = str(uuid4())
    
    get_global_ttl_cache()[token] = edupage

    return {"response": token}

@app.get("/timetable")
@logged_in
@returns_edupage_object
@authenticated
def get_timetable(edupage: Edupage, date: date):
    if not edupage.is_logged_in:
        raise HTTPException(status_code=400, detail="You first have to log in")
    
    return edupage.get_timetable(date)

@app.get("/students")
@logged_in
@authenticated
@returns_edupage_object
def get_students(edupage: Edupage):
    return edupage.get_all_students()

@app.get("/teachers")
@logged_in
@returns_edupage_object
@authenticated
def get_teachers(edupage: Edupage):
    return edupage.get_teachers()

@app.post("/message")
@authenticated
def send_message(edupage: Edupage, message: Message):
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
@authenticated
def get_lunches(edupage: Edupage, date: date):
    return edupage.get_lunches(date)

@app.post("/lunches")
@logged_in
@authenticated
def change_lunch(edupage: Edupage, date: date, choice: int):
    lunches = edupage.get_lunches(date)
    lunches.choose(edupage, choice)

    return {"response": "Ok"}

@app.delete("/lunches")
@logged_in
@authenticated
def cancel_lunch(edupage: Edupage, date: date):
    lunches = edupage.get_lunches(date)
    lunches.sign_off(edupage)
    
    return {"response": "Ok"}

@app.get("/timeline")
@logged_in
@returns_edupage_object
@ttl_cache(maxsize=20, ttl=100)
@authenticated
def get_timeline(edupage: Edupage, items_per_page: int, page: int):
    timeline = edupage.get_notifications()

    try:
        output = []
        for i in range(page * items_per_page, page * items_per_page + items_per_page):
            output.append(timeline[i])
    
        return output
    except IndexError:
        if len(output) == 0:
            raise HTTPException(status_code=204)
        else:
            return output

@app.post("cloud-upload")
@returns_edupage_object
@logged_in
@authenticated
def cloud_upload(edupage: Edupage, file: bytes = File(default=None)):
    if file is None:
        raise HTTPException(status_code=400, detail="No file sent!")

    return edupage.cloud_upload(BytesIO(file))

@app.get("/grades")
@returns_edupage_object
@logged_in
@authenticated
def get_grades(edupage: Edupage):
    return edupage.get_grades()

@app.get("/missing-teachers")
@logged_in
@returns_edupage_object
@authenticated
def get_missing_teachers(edupage: Edupage, date: date):
    return edupage.get_missing_teachers(date)

@app.get("/timetable-changes")
@returns_edupage_object
@logged_in
@authenticated
def get_timetable_changes(edupage: Edupage, date: date):
    return edupage.get_timetable_changes(date)

@app.get("/school-year")
@logged_in
@authenticated
def get_school_year(edupage: Edupage):
    return edupage.get_school_year()

@app.get("/foreign-timetable")
@logged_in
@returns_edupage_object
@authenticated
def get_foreign_timetable(edupage: Edupage, id: int, date: date):
    try:
        return edupage.get_foreign_timetable(id, date)
    except MissingDataException as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/next-ringing")
@logged_in
@returns_edupage_object
@authenticated
def get_next_ringing_time(edupage: Edupage, datetime: datetime):
    return edupage.get_next_ringing_time(datetime)