# Sistema de Login Personalizado - Presenton

## 🎨 Cambios Implementados

Se ha reemplazado el sistema de autenticación HTTP Basic (popup feo del navegador) con un **sistema moderno de login con página personalizada** usando JWT (JSON Web Tokens).

---

## ✨ Características del Nuevo Sistema

### 🎯 Página de Login Profesional
- Diseño moderno y responsivo
- Gradientes y animaciones suaves
- Iconos SVG integrados
- Mensajes de error claros
- Estados de carga (loading)
- Totalmente personalizable

### 🔐 Autenticación JWT
- Tokens seguros con firma
- Sesiones de 24 horas por defecto (configurable)
- Almacenamiento en cookies HTTP-only
- Protección contra CSRF
- Renovación automática de sesión

### 🛡️ Seguridad
- Middleware de autenticación en FastAPI
- Provider de autenticación en Next.js
- Redirección automática a login si no autenticado
- Protección de todas las rutas (excepto `/login`)

---

## 📁 Archivos Creados/Modificados

### Backend (FastAPI)

#### Nuevos Archivos:
1. **`/servers/fastapi/core/auth.py`**
   - Sistema de JWT con jose
   - Hash de contraseñas con bcrypt
   - Generación y verificación de tokens
   - Duración: 24 horas por defecto

2. **`/servers/fastapi/models/auth.py`**
   - `LoginRequest`: Modelo para credenciales
   - `TokenResponse`: Respuesta con token JWT

3. **`/servers/fastapi/api/v1/auth/endpoints.py`**
   - `POST /api/v1/auth/login`: Endpoint de login
   - `POST /api/v1/auth/logout`: Endpoint de logout
   - `GET /api/v1/auth/me`: Verificar sesión actual

4. **`/servers/fastapi/api/v1/auth/router.py`**
   - Router para endpoints de autenticación

#### Archivos Modificados:
1. **`/servers/fastapi/api/middlewares.py`**
   - Cambiado de HTTP Basic Auth a JWT
   - Verifica token en cookies o header Authorization
   - Rutas públicas: `/login`, `/logout`, `/docs`

2. **`/servers/fastapi/api/main.py`**
   - Agregado router de autenticación

### Frontend (Next.js)

#### Nuevos Archivos:
1. **`/servers/nextjs/app/login/page.tsx`**
   - Página de login moderna y profesional
   - Diseño con Tailwind CSS
   - Validación de formulario
   - Manejo de errores
   - Estados de carga

2. **`/servers/nextjs/components/AuthProvider.tsx`**
   - Componente que protege todas las rutas
   - Verifica autenticación en cada navegación
   - Redirige a `/login` si no autenticado

#### Archivos Modificados:
1. **`/servers/nextjs/app/layout.tsx`**
   - Integrado `AuthProvider` para proteger toda la app

---

## 🎨 Diseño de la Página de Login

### Características Visuales:
- **Fondo**: Gradiente suave (azul → blanco → morado) con patrón de cuadrícula
- **Card**: Blanco con sombra elevada y bordes redondeados
- **Logo**: Icono de documento en gradiente azul-morado
- **Campos**: Input con iconos (usuario, candado)
- **Botón**: Gradiente azul-morado con efecto hover
- **Animaciones**: Transiciones suaves en todos los elementos
- **Responsive**: Adaptable a móvil, tablet y desktop

### Flujo de Usuario:
1. Usuario abre `http://localhost:5000`
2. Sistema detecta que no está autenticado
3. Redirige automáticamente a `/login`
4. Usuario ingresa credenciales
5. Si son correctas: Redirige a la página principal
6. Si son incorrectas: Muestra error en rojo

---

## 🔧 Configuración

### Variables de Entorno (`.env`)

```bash
# Credenciales del sistema
AUTH_USERNAME=zucaritas
AUTH_PASSWORD=g3st24mWork5

# Secret key para JWT (opcional, se genera automáticamente si está vacío)
JWT_SECRET_KEY=

# Tiempo de expiración del token en minutos (default: 1440 = 24 horas)
JWT_EXPIRE_MINUTES=1440
```

### Generar Secret Key Segura

Para producción, genera una clave secreta:

```bash
openssl rand -hex 32
```

Luego agrégala al `.env`:
```bash
JWT_SECRET_KEY=tu_clave_secreta_de_64_caracteres_aqui
```

---

## 🚀 Cómo Usar

### Acceder a la Aplicación

1. **Abre tu navegador**: `http://localhost:5000`
2. **Serás redirigido a**: `http://localhost:5000/login`
3. **Ingresa las credenciales**:
   - Usuario: `zucaritas`
   - Contraseña: `g3st24mWork5`
4. **Haz clic en**: "Iniciar Sesión"
5. **Serás redirigido** a la página principal

### Cerrar Sesión

Actualmente el logout se hace limpiando las cookies. Para cerrar sesión manualmente:

```bash
curl -X POST http://localhost:5000/api/v1/auth/logout -c cookies.txt -b cookies.txt
```

O desde el navegador, abre la consola y ejecuta:
```javascript
fetch('/api/v1/auth/logout', { method: 'POST', credentials: 'include' })
  .then(() => window.location.href = '/login');
```

---

## 🧪 Pruebas del Sistema

### Probar Login con cURL

**Login exitoso:**
```bash
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"zucaritas","password":"g3st24mWork5"}'
```

**Respuesta esperada:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "username": "zucaritas"
}
```

**Login fallido:**
```bash
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"zucaritas","password":"wrong"}'
```

**Respuesta esperada:**
```json
{
  "detail": "Usuario o contraseña incorrectos"
}
```

### Probar Acceso Protegido

**Sin token (debe fallar):**
```bash
curl http://localhost:5000/api/v1/ppt/presentations
```

**Respuesta:**
```json
{
  "detail": "No autenticado. Por favor inicia sesión."
}
```

**Con token (debe funcionar):**
```bash
# Primero obtener el token
TOKEN=$(curl -s -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"zucaritas","password":"g3st24mWork5"}' | jq -r '.access_token')

# Usar el token
curl -H "Authorization: Bearer $TOKEN" http://localhost:5000/api/v1/ppt/presentations
```

---

## 🎯 Endpoints de Autenticación

### POST `/api/v1/auth/login`
Iniciar sesión y obtener token JWT.

**Request:**
```json
{
  "username": "zucaritas",
  "password": "g3st24mWork5"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "username": "zucaritas"
}
```

**Response (401):**
```json
{
  "detail": "Usuario o contraseña incorrectos"
}
```

### POST `/api/v1/auth/logout`
Cerrar sesión (elimina cookie).

**Response (200):**
```json
{
  "message": "Logout exitoso"
}
```

### GET `/api/v1/auth/me`
Verificar sesión actual (requiere autenticación).

**Response (200):**
```json
{
  "message": "Usuario autenticado"
}
```

**Response (401):**
```json
{
  "detail": "No autenticado. Por favor inicia sesión."
}
```

---

## 🔒 Seguridad Implementada

### En el Backend (FastAPI)

1. **JWT con HS256**: Tokens firmados con clave secreta
2. **Bcrypt**: Hash seguro para comparación de contraseñas
3. **Expiración de Tokens**: 24 horas por defecto
4. **Cookies HTTP-Only**: No accesibles desde JavaScript
5. **Middleware**: Valida token en cada petición
6. **Rutas Públicas**: Solo login y documentación

### En el Frontend (Next.js)

1. **AuthProvider**: Protege todas las rutas
2. **Verificación Automática**: En cada cambio de ruta
3. **Redirección**: A `/login` si no autenticado
4. **LocalStorage**: Guarda token para persistencia
5. **Cookies**: También usa cookies para mayor seguridad

---

## 📝 Personalización

### Cambiar Diseño del Login

Edita: `/servers/nextjs/app/login/page.tsx`

**Colores del gradiente:**
```tsx
className="bg-gradient-to-br from-blue-50 via-white to-purple-50"
className="bg-gradient-to-r from-blue-600 to-purple-600"
```

**Logo/Icono:**
```tsx
<svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
  {/* Cambia el path del SVG aquí */}
</svg>
```

**Textos:**
```tsx
<h1 className="text-3xl font-bold text-gray-900 mb-2">Presenton</h1>
<p className="text-gray-600">Bienvenido de vuelta</p>
```

### Cambiar Duración de Sesión

En `.env`:
```bash
# 12 horas
JWT_EXPIRE_MINUTES=720

# 7 días
JWT_EXPIRE_MINUTES=10080
```

### Agregar Más Usuarios

Actualmente solo soporta un usuario (desde `.env`). Para múltiples usuarios necesitarías:

1. Crear tabla de usuarios en MySQL
2. Modificar `core/auth.py` para buscar en BD
3. Agregar endpoint de registro
4. Hash de contraseñas al guardar

---

## ✅ Estado Final

### Backend
- ✅ Endpoints de autenticación funcionando
- ✅ JWT con expiración
- ✅ Middleware protegiendo rutas
- ✅ Cookies HTTP-only

### Frontend
- ✅ Página de login profesional
- ✅ AuthProvider protegiendo rutas
- ✅ Redirección automática
- ✅ Manejo de errores

### Integración
- ✅ Next.js y FastAPI comunicándose
- ✅ Cookies compartidas entre servicios
- ✅ Tokens validándose correctamente
- ✅ Sesiones persistiendo

---

## 🎉 Resultado

Ahora cuando alguien acceda a `http://localhost:5000` verá una **página de login moderna y profesional** en lugar del popup feo del navegador. El sistema es:

- ✨ **Bonito**: Diseño profesional con gradientes y animaciones
- 🔒 **Seguro**: JWT, cookies HTTP-only, middleware
- 🚀 **Rápido**: Validación en frontend y backend
- 📱 **Responsive**: Funciona en móvil, tablet y desktop
- 🎨 **Personalizable**: Fácil de modificar colores y estilos

---

## 📅 Fecha de Implementación
**Abril 17, 2026**
