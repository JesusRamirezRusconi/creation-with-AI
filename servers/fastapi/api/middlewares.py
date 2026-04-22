import base64
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse
from fastapi import status
import os

from utils.get_env import get_can_change_keys_env
from utils.user_config import update_env_with_user_config
from core.auth import verify_token


class UserConfigEnvUpdateMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if get_can_change_keys_env() != "false":
            update_env_with_user_config()
        return await call_next(request)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware para autenticación JWT
    Verifica token en cookies o header Authorization
    """
    
    # Rutas que NO requieren autenticación
    EXCLUDED_PATHS = [
        "/docs",
        "/redoc",
        "/openapi.json",
        "/health",
        "/api/v1/auth/login",  # Login debe ser público
        "/api/v1/auth/logout",  # Logout debe ser público
    ]
    
    async def dispatch(self, request: Request, call_next):
        # Verificar si la ruta está excluida
        if any(request.url.path.startswith(path) for path in self.EXCLUDED_PATHS):
            return await call_next(request)
        
        # Intentar obtener token de la cookie
        token = request.cookies.get("access_token")
        
        # Si no hay cookie, intentar obtener del header Authorization
        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
        else:
            # Si viene de cookie, quitar el prefijo "Bearer "
            if token.startswith("Bearer "):
                token = token.split(" ")[1]
        
        # Si no hay token, devolver 401
        if not token:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "No autenticado. Por favor inicia sesión."}
            )
        
        # Verificar el token
        user_data = verify_token(token)
        
        if not user_data:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Token inválido o expirado"}
            )
        
        # Agregar usuario al request state
        request.state.user = user_data.get("username")
        
        # Continuar con la petición
        response = await call_next(request)
        return response
