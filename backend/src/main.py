from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routes.events.routes import admin_router as admin_events_router
from src.routes.events.routes import router as events_router
from src.routes.attachments import admin_router as admin_attachments_router
from src.routes.attachments import router as attachments_router
from src.routes.informations.routes import admin_router as admin_informations_router
from src.routes.informations.routes import router as informations_router
from src.routes.journal.routes import router as journal_router
from src.routes.journal.routes import admin_router as journal_admin_router
from src.routes.portal.routes import router as portal_router
from src.routes.ticket.routes import admin_router as ticket_admin_router
from src.routes.ticket.routes import router as ticket_router
from src.routes.webadmin.routes import router as auth_router

app = FastAPI(title="Site-Caesi Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(attachments_router)
app.include_router(admin_attachments_router)
app.include_router(ticket_router)
app.include_router(ticket_admin_router)
app.include_router(journal_router)
app.include_router(journal_admin_router)
app.include_router(informations_router)
app.include_router(admin_informations_router)
app.include_router(events_router)
app.include_router(admin_events_router)
app.include_router(portal_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
