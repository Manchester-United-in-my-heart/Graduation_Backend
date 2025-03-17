from fastapi import FastAPI
import models
from database import engine
from routers import login, register, users, projects, published_books, secret
from fastapi.middleware.cors import CORSMiddleware

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins="*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(register.router)
app.include_router(login.router)
app.include_router(users.router)
app.include_router(published_books.router, prefix="/published_books", tags=["published_books"])
app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(secret.router, prefix="/secret", tags=["secret"])