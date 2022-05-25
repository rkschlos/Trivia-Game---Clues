from fastapi import FastAPI

from routers import categories
from routers import clues

app = FastAPI()

# Using routers for organization
# See https://fastapi.tiangolo.com/tutorial/bigger-applications/
app.include_router(categories.router)
app.include_router(clues.router)