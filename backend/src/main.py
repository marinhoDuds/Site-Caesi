from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routes.ticket.routes import router as ticket_router
from src.routes.ticket.routes import admin_router as ticket_admin_router
from src.routes.journal.routes import router as journal_router
from src.routes.journal.routes import admin_router as journal_admin_router
from src.routes.informations.routes import router as informations_router, admin_router as admin_informations_router

app = FastAPI(title="Site-Caesi Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ticket_router)
app.include_router(ticket_admin_router)
app.include_router(journal_router)
app.include_router(journal_admin_router)
app.include_router(informations_router)
app.include_router(admin_informations_router)

# TODO: Include other routers as they are built (portal, etc.)

@app.get("/health")
def health_check():
    return {"status": "ok"}
