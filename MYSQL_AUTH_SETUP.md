# Configuración de MySQL y Autenticación - Presenton

## 📋 Resumen de Cambios

Se han implementado dos mejoras principales en el proyecto:

1. **Migración de SQLite a MySQL**
2. **Sistema de Autenticación HTTP Basic**

---

## 🗄️ Configuración de MySQL

### Cambios Realizados

#### 1. Archivo `.env`
- Se configuró `DATABASE_URL` para conectarse a MySQL
- La conexión usa la IP del gateway de Docker: `172.23.0.1`
- Formato: `mysql+aiomysql://root:1234jesus@172.23.0.1:3306/jesus`

#### 2. Base de Datos Creada
- **Nombre**: `jesus`
- **Usuario**: `root`
- **Contraseña**: `1234jesus`
- **Charset**: `utf8mb4_unicode_ci`

#### 3. Modelos Actualizados
Se modificó `models/sql/presentation.py` para compatibilidad con MySQL:
- Campos `VARCHAR` ahora tienen longitud definida
- Campo `content` cambiado de `VARCHAR` a `TEXT` para soportar contenido largo
- Campos actualizados:
  - `content`: TEXT
  - `language`: VARCHAR(50)
  - `title`: VARCHAR(500)
  - `instructions`: VARCHAR(2000)
  - `tone`: VARCHAR(100)
  - `verbosity`: VARCHAR(100)

#### 4. Docker Compose
Se agregó `extra_hosts` para permitir conexión del contenedor al host:
```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

---

## 🔐 Sistema de Autenticación

### Credenciales Configuradas
- **Usuario**: `zucaritas`
- **Contraseña**: `g3st24mWork5`

### Archivos Creados

#### 1. `/servers/fastapi/core/security.py`
Funciones de seguridad:
- `hash_password()`: Hash SHA256 de contraseñas
- `verify_password()`: Verificación de contraseñas
- `get_auth_credentials()`: Obtiene credenciales desde `.env`
- `verify_credentials()`: Dependency para FastAPI

#### 2. `/servers/fastapi/models/sql/user.py`
Modelo de usuario para futuras implementaciones:
- Campos: id, username, hashed_password, is_active, created_at, last_login

#### 3. `/servers/fastapi/api/middlewares.py` (actualizado)
Se agregó `AuthenticationMiddleware`:
- Intercepta todas las peticiones
- Valida credenciales HTTP Basic
- Rutas excluidas: `/docs`, `/redoc`, `/openapi.json`, `/health`

#### 4. `/servers/fastapi/api/main.py` (actualizado)
Se agregó el middleware de autenticación a la aplicación FastAPI

### Cómo Funciona

1. **Todas las rutas requieren autenticación** excepto las documentadas
2. **HTTP Basic Auth**: El navegador mostrará un popup pidiendo usuario y contraseña
3. **Respuestas**:
   - Sin credenciales: `401 Unauthorized`
   - Credenciales incorrectas: `401 Unauthorized`
   - Credenciales correctas: Acceso permitido

### Pruebas Realizadas

```bash
# Sin autenticación → 401
curl http://localhost:5000/api/v1/ppt/presentations

# Con credenciales correctas → Acceso permitido
curl -u zucaritas:g3st24mWork5 http://localhost:5000/api/v1/ppt/presentations

# Con credenciales incorrectas → 401
curl -u zucaritas:wrongpass http://localhost:5000/api/v1/ppt/presentations
```

---

## 📝 Variables de Entorno Nuevas

### En `.env`
```bash
# Autenticación
AUTH_USERNAME=zucaritas
AUTH_PASSWORD=g3st24mWork5

# Base de Datos MySQL
DATABASE_URL=mysql+aiomysql://root:1234jesus@172.23.0.1:3306/jesus
```

### En `docker-compose.yml`
Se agregaron las variables al servicio `development`:
```yaml
environment:
  - AUTH_USERNAME=${AUTH_USERNAME}
  - AUTH_PASSWORD=${AUTH_PASSWORD}
```

---

## ✅ Estado Final

### MySQL
- ✅ Conexión exitosa desde el contenedor
- ✅ Base de datos `jesus` creada
- ✅ Modelos compatibles con MySQL
- ✅ Aplicación arrancando correctamente

### Autenticación
- ✅ Middleware implementado
- ✅ Credenciales desde `.env`
- ✅ Protección en todas las rutas
- ✅ HTTP Basic Auth funcionando

### Docker
- ✅ Contenedor iniciado correctamente
- ✅ FastAPI: `http://localhost:8000`
- ✅ Next.js: `http://localhost:3000`
- ✅ Nginx: `http://localhost:5000`

---

## 🚀 Cómo Usar

### Acceder a la Aplicación
1. Abre tu navegador en `http://localhost:5000`
2. Se mostrará un popup de autenticación
3. Ingresa:
   - **Usuario**: `zucaritas`
   - **Contraseña**: `g3st24mWork5`
4. ¡Listo! Ya puedes usar la aplicación

### Cambiar Credenciales
1. Edita el archivo `.env`:
   ```bash
   AUTH_USERNAME=nuevo_usuario
   AUTH_PASSWORD=nueva_contraseña
   ```
2. Reinicia Docker:
   ```bash
   docker-compose restart development
   ```

### Verificar Tablas en MySQL
```bash
mysql -u root -p1234jesus -h localhost -e "USE jesus; SHOW TABLES;"
```

---

## 📚 Documentación Adicional

- **Modelos SQL**: `/servers/fastapi/models/sql/`
- **Seguridad**: `/servers/fastapi/core/security.py`
- **Middlewares**: `/servers/fastapi/api/middlewares.py`
- **Configuración**: `.env` y `.env.example`

---

## 🔧 Solución de Problemas

### Error: "Can't connect to MySQL server"
- Verifica que MySQL esté corriendo en tu host
- Verifica las credenciales en `.env`
- Verifica que la IP del gateway sea correcta (usa `docker network inspect presenton_default`)

### Error: "Authentication required"
- Asegúrate de que las variables `AUTH_USERNAME` y `AUTH_PASSWORD` estén en `.env`
- Reinicia Docker después de cambiar credenciales

### Error: "VARCHAR requires a length"
- Ya está solucionado en los modelos actuales
- Si creas nuevos modelos, usa `String(longitud)` o `Text`

---

## 📅 Fecha de Implementación
**Abril 17, 2026**
