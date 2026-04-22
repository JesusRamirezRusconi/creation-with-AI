from fastapi import APIRouter, HTTPException, status, Response
from models.auth import LoginRequest, TokenResponse
from core.auth import verify_user_credentials, create_access_token
from datetime import timedelta

AUTH_ROUTER = APIRouter(prefix="/auth", tags=["Authentication"])


@AUTH_ROUTER.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest, response: Response):
    """
    Endpoint de login - Devuelve un JWT token si las credenciales son correctas
    """
    # Verificar credenciales
    if not verify_user_credentials(credentials.username, credentials.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
        )
    
    # Crear token JWT
    access_token = create_access_token(
        data={"sub": credentials.username},
        expires_delta=timedelta(hours=24)
    )
    
    # También establecer cookie para el navegador
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=86400,  # 24 horas
        samesite="lax"
    )
    
    return TokenResponse(
        access_token=access_token,
        username=credentials.username
    )


@AUTH_ROUTER.post("/logout")
async def logout(response: Response):
    """
    Endpoint de logout - Elimina la cookie del token
    """
    response.delete_cookie(key="access_token")
    return {"message": "Logout exitoso"}


@AUTH_ROUTER.get("/me")
async def get_current_user():
    """
    Obtener información del usuario actual (requiere autenticación)
    """
    # Este endpoint será protegido por el middleware
    return {"message": "Usuario autenticado"}
