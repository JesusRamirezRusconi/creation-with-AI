from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.lifespan import app_lifespan
from api.middlewares import UserConfigEnvUpdateMiddleware, AuthenticationMiddleware
from api.v1.ppt.router import API_V1_PPT_ROUTER
from api.v1.webhook.router import API_V1_WEBHOOK_ROUTER
from api.v1.mock.router import API_V1_MOCK_ROUTER
from api.v1.auth.router import API_V1_AUTH_ROUTER


app = FastAPI(lifespan=app_lifespan)


# Routers
app.include_router(API_V1_AUTH_ROUTER)  # Auth debe ir primero (antes de protección)
app.include_router(API_V1_PPT_ROUTER)
app.include_router(API_V1_WEBHOOK_ROUTER)
app.include_router(API_V1_MOCK_ROUTER)

# Middlewares
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication middleware (DEBE IR PRIMERO)
app.add_middleware(AuthenticationMiddleware)

app.add_middleware(UserConfigEnvUpdateMiddleware)
