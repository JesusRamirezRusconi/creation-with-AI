<p align="center">
  <img src="readme_assets/images/presenton-logo.png" height="90" alt="Logo de Presenton" />
</p>

<p align="center">
  <a href="https://discord.gg/9ZsKKxudNE">
    <img src="https://img.shields.io/badge/Discord-Únete%20a%20la%20Comunidad-5865F2?logo=discord&style=for-the-badge" alt="Únete a nuestro Discord" />
  </a>
  &nbsp;
  <a href="https://x.com/presentonai">
    <img src="https://img.shields.io/badge/X-Síguenos-000000?logo=twitter&style=for-the-badge" alt="Síguenos en X" />
  </a>
</p>

# Generador de Presentaciones con IA de Código Abierto (Alternativa a Gamma, Beautiful AI, Decktopus)

**Presenton** es una aplicación de código abierto para generar presentaciones con inteligencia artificial — todo ejecutándose localmente en tu dispositivo. Mantén el control de tus datos y privacidad mientras usas modelos como OpenAI y Gemini, o utiliza tus propios modelos alojados a través de Ollama.

__✨ ¡Ahora puedes generar presentaciones con tu archivo PPTX existente! Solo sube tu archivo de presentación para crear un diseño de plantilla y luego usa esa plantilla para generar presentaciones con tu marca y diseño sobre cualquier tema.__

![Demo](readme_assets/demo.gif)

> [!NOTE]
> **Consultas Empresariales:**
> Para uso empresarial, implementaciones personalizadas u oportunidades de asociación, contáctanos en **[suraj@presenton.ai](mailto:suraj@presenton.ai)**.

> [!IMPORTANT]
> ¿Te gusta Presenton? ¡Una ⭐ estrella muestra tu apoyo y nos anima a seguir construyendo!

> [!TIP]
> Para guías de configuración detalladas, documentación de la API y opciones de configuración avanzadas, visita nuestra **[Documentación Oficial](https://docs.presenton.ai)**

## 🚀 Tecnologías Utilizadas

Presenton está construido con tecnologías modernas y robustas:

### Backend
- **Python 3.11** - Lenguaje principal del backend
- **FastAPI** - Framework web moderno y rápido para APIs
- **SQLModel** - ORM moderno basado en SQLAlchemy y Pydantic
- **Bases de datos soportadas**: SQLite (por defecto), PostgreSQL, MySQL
- **Ollama** - Para ejecutar modelos de IA localmente

### Frontend
- **Next.js 14** - Framework de React para aplicaciones web
- **React 18** - Biblioteca de interfaz de usuario
- **TypeScript** - Tipado estático para JavaScript
- **Tailwind CSS** - Framework de CSS utilitario
- **Radix UI** - Componentes de interfaz accesibles
- **Redux Toolkit** - Gestión de estado

### Infraestructura
- **Docker & Docker Compose** - Contenedorización y orquestación
- **Nginx** - Servidor web y proxy reverso
- **Node.js 20** - Runtime de JavaScript

### Integraciones de IA
- **OpenAI** (GPT-4, DALL-E 3)
- **Google Gemini** (Gemini 2.0 Flash)
- **Anthropic Claude** (Claude 3.5 Sonnet)
- **Ollama** (Modelos locales como Llama 3.2)
- **APIs compatibles con OpenAI**

### Generación de Contenido
- **Python-PPTX** - Creación de archivos PowerPoint
- **Puppeteer** - Generación de PDFs
- **Docling** - Procesamiento de documentos
- **ChromaDB** - Base de datos vectorial para búsqueda semántica

## ✨ Más Libertad con Presentaciones de IA

Presenton te da control completo sobre tu flujo de trabajo de presentaciones con IA. Elige tus modelos, personaliza tu experiencia y mantén tus datos privados.

* ✅ **Plantillas y Temas Personalizados** — Crea diseños de presentación ilimitados con HTML y Tailwind CSS
* ✅ **Generación de Plantillas con IA** — Crea plantillas de presentación desde documentos de PowerPoint existentes
* ✅ **Generación Flexible** — Construye presentaciones desde prompts o documentos subidos
* ✅ **Listo para Exportar** — Guarda como PowerPoint (PPTX) y PDF con formato profesional
* ✅ **Servidor MCP Integrado** — Genera presentaciones a través del Protocolo de Contexto de Modelo
* ✅ **Trae Tu Propia Clave** — Usa tus propias claves API para OpenAI, Google Gemini, Anthropic Claude, o cualquier proveedor compatible. Solo paga por lo que uses, sin tarifas ocultas o suscripciones
* ✅ **Integración con Ollama** — Ejecuta modelos de código abierto localmente con privacidad completa
* ✅ **Compatible con API de OpenAI** — Conéctate a cualquier endpoint compatible con OpenAI con tus propios modelos
* ✅ **Soporte Multi-Proveedor** — Mezcla y combina proveedores de generación de texto e imágenes
* ✅ **Generación de Imágenes Versátil** — Elige entre DALL-E 3, Gemini Flash, Pexels, o Pixabay
* ✅ **Soporte de Medios Enriquecidos** — Iconos, gráficos y gráficos personalizados para presentaciones profesionales
* ✅ **Ejecuta Localmente** — Todo el procesamiento ocurre en tu dispositivo, sin dependencias en la nube
* ✅ **Implementación de API** — Aloja como tu propio servicio API para tu equipo
* ✅ **Completamente de Código Abierto** — Licencia Apache 2.0, inspecciona, modifica y contribuye
* ✅ **Listo para Docker** — Implementación con un comando con soporte GPU para modelos locales

## 🛠️ Instalación y Configuración desde Cero

### Prerrequisitos

Antes de comenzar, asegúrate de tener instalado:

- **Docker** y **Docker Compose** (recomendado)
- O alternativamente: **Python 3.11**, **Node.js 20**, **npm**

### Método 1: Instalación con Docker (Recomendado)

#### 1. Ejecutar Presenton

##### Linux/MacOS (Bash/Zsh Shell):
```bash
docker run -it --name presenton -p 5000:80 -v "./app_data:/app_data" ghcr.io/presenton/presenton:latest
```

##### Windows (PowerShell):
```bash
docker run -it --name presenton -p 5000:80 -v "${PWD}\app_data:/app_data" ghcr.io/presenton/presenton:latest
```

#### 2. Abrir Presenton
Abre http://localhost:5000 en el navegador de tu elección para usar Presenton.

> **Nota: Puedes reemplazar 5000 con cualquier otro número de puerto de tu elección para ejecutar Presenton en un puerto diferente.**

### Método 2: Instalación Manual (Desarrollo)

#### 1. Clonar el repositorio
```bash
git clone https://github.com/presenton/presenton.git
cd presenton
```

#### 2. Configurar el backend (FastAPI)
```bash
cd servers/fastapi
pip install -r requirements.txt
# O usando uv (recomendado)
uv sync
```

#### 3. Configurar el frontend (Next.js)
```bash
cd ../nextjs
npm install
npm run build
```

#### 4. Ejecutar en modo desarrollo
```bash
# Desde la raíz del proyecto
node start.js --dev
```

### Método 3: Docker Compose (Para desarrollo)

```bash
# Producción
docker-compose up production

# Desarrollo
docker-compose up development

# Con soporte GPU
docker-compose up production-gpu
```

## ⚙️ Configuraciones de Implementación

Puedes proporcionar directamente tus CLAVES API como variables de entorno y mantenerlas ocultas. Puedes establecer estas variables de entorno para lograrlo.

### Variables de Entorno Principales

- **CAN_CHANGE_KEYS=[true/false]**: Establece esto en **false** si quieres mantener las claves API ocultas e inmutables.
- **LLM=[openai/google/anthropic/ollama/custom]**: Selecciona el **LLM** de tu elección.
- **OPENAI_API_KEY=[Tu Clave API de OpenAI]**: Proporciona esto si **LLM** está configurado como **openai**
- **OPENAI_MODEL=[ID del Modelo OpenAI]**: Proporciona esto si **LLM** está configurado como **openai** (por defecto: "gpt-4o-mini")
- **GOOGLE_API_KEY=[Tu Clave API de Google]**: Proporciona esto si **LLM** está configurado como **google**
- **GOOGLE_MODEL=[ID del Modelo Google]**: Proporciona esto si **LLM** está configurado como **google** (por defecto: "models/gemini-2.0-flash")
- **ANTHROPIC_API_KEY=[Tu Clave API de Anthropic]**: Proporciona esto si **LLM** está configurado como **anthropic**
- **ANTHROPIC_MODEL=[ID del Modelo Anthropic]**: Proporciona esto si **LLM** está configurado como **anthropic** (por defecto: "claude-3-5-sonnet-20241022")
- **OLLAMA_URL=[URL Personalizada de Ollama]**: Proporciona esto si quieres una URL personalizada de Ollama y **LLM** está configurado como **ollama**
- **OLLAMA_MODEL=[ID del Modelo Ollama]**: Proporciona esto si **LLM** está configurado como **ollama**
- **CUSTOM_LLM_URL=[URL Compatible con OpenAI Personalizada]**: Proporciona esto si **LLM** está configurado como **custom**
- **CUSTOM_LLM_API_KEY=[CLAVE API Compatible con OpenAI Personalizada]**: Proporciona esto si **LLM** está configurado como **custom**
- **CUSTOM_MODEL=[ID del Modelo Personalizado]**: Proporciona esto si **LLM** está configurado como **custom**

### Variables de Entorno para Imágenes

- **IMAGE_PROVIDER=[pexels/pixabay/gemini_flash/dall-e-3]**: Selecciona el proveedor de imágenes de tu elección.
- **PEXELS_API_KEY=[Tu Clave API de Pexels]**: Requerida si usas **pexels** como proveedor de imágenes.
- **PIXABAY_API_KEY=[Tu Clave API de Pixabay]**: Requerida si usas **pixabay** como proveedor de imágenes.

### Ejemplos de Configuración

#### Usando OpenAI
```bash
docker run -it --name presenton -p 5000:80 \
  -e LLM="openai" \
  -e OPENAI_API_KEY="tu-clave-api" \
  -e IMAGE_PROVIDER="dall-e-3" \
  -e CAN_CHANGE_KEYS="false" \
  -v "./app_data:/app_data" \
  ghcr.io/presenton/presenton:latest
```

#### Usando Google Gemini
```bash
docker run -it --name presenton -p 5000:80 \
  -e LLM="google" \
  -e GOOGLE_API_KEY="tu-clave-api" \
  -e IMAGE_PROVIDER="gemini_flash" \
  -e CAN_CHANGE_KEYS="false" \
  -v "./app_data:/app_data" \
  ghcr.io/presenton/presenton:latest
```

#### Usando Ollama (Modelos Locales)
```bash
docker run -it --name presenton -p 5000:80 \
  -e LLM="ollama" \
  -e OLLAMA_MODEL="llama3.2:3b" \
  -e IMAGE_PROVIDER="pexels" \
  -e PEXELS_API_KEY="tu-clave-api" \
  -e CAN_CHANGE_KEYS="false" \
  -v "./app_data:/app_data" \
  ghcr.io/presenton/presenton:latest
```

#### Ejecutar Presenton con Soporte GPU

Para usar aceleración GPU con modelos Ollama, necesitas instalar y configurar el NVIDIA Container Toolkit. Una vez instalado, puedes ejecutar Presenton con soporte GPU agregando la bandera `--gpus=all`:

```bash
docker run -it --name presenton --gpus=all -p 5000:80 \
  -e LLM="ollama" \
  -e OLLAMA_MODEL="llama3.2:3b" \
  -e IMAGE_PROVIDER="pexels" \
  -e PEXELS_API_KEY="tu-clave-api" \
  -e CAN_CHANGE_KEYS="false" \
  -v "./app_data:/app_data" \
  ghcr.io/presenton/presenton:latest
```

> **Nota:** La aceleración GPU mejora significativamente el rendimiento de los modelos Ollama, especialmente para modelos más grandes. Asegúrate de tener suficiente memoria GPU para tu modelo elegido.

## 📋 Funcionalidades Principales

### 1. Generación de Presentaciones con IA
- **Generación desde prompts**: Describe tu tema y deja que la IA cree la presentación completa
- **Carga de documentos**: Sube archivos PDF, DOCX, PPTX para generar presentaciones basadas en el contenido
- **Plantillas personalizables**: Más de 10 temas prediseñados con capacidad de crear plantillas personalizadas
- **Múltiples idiomas**: Soporte para más de 50 idiomas incluyendo español, inglés, francés, alemán, etc.

### 2. Edición y Personalización
- **Editor visual**: Interfaz intuitiva para editar diapositivas en tiempo real
- **Cambio de temas**: Cambia el diseño de toda la presentación con un clic
- **Edición de contenido**: Modifica texto, imágenes y elementos gráficos fácilmente
- **Reorganización**: Arrastra y suelta diapositivas para reorganizar el orden

### 3. Generación de Contenido Multimedia
- **Imágenes con IA**: Genera imágenes personalizadas usando DALL-E 3, Gemini Flash
- **Imágenes de stock**: Integración con Pexels y Pixabay para imágenes profesionales
- **Iconos y gráficos**: Biblioteca extensa de iconos y elementos gráficos
- **Gráficos y tablas**: Crea visualizaciones de datos automáticamente

### 4. Exportación y Presentación
- **Formato PPTX**: Exporta a PowerPoint nativo para edición posterior
- **Formato PDF**: Genera PDFs de alta calidad para distribución
- **Modo presentación**: Presenta directamente desde la aplicación web
- **Vista previa**: Revisa tu presentación antes de exportar

### 5. API REST Completa
- **Generación programática**: Crea presentaciones via API REST
- **Integración empresarial**: Integra con tus sistemas existentes
- **Webhooks**: Recibe notificaciones de eventos
- **Documentación completa**: API totalmente documentada

### 6. Configuración Flexible
- **Múltiples proveedores de IA**: OpenAI, Google, Anthropic, Ollama, APIs personalizadas
- **Configuración de tono**: Casual, profesional, educativo, divertido, pitch de ventas
- **Nivel de detalle**: Conciso, estándar, rico en texto
- **Búsqueda web**: Integra información actualizada de internet

## 🎯 Casos de Uso

### Para Empresas
- **Presentaciones de ventas**: Genera pitches personalizados para clientes
- **Reportes ejecutivos**: Crea informes profesionales automáticamente
- **Capacitación**: Desarrolla material educativo para empleados
- **Marketing**: Presenta productos y servicios de manera atractiva

### Para Educación
- **Clases y conferencias**: Crea material didáctico interactivo
- **Investigación**: Presenta hallazgos y datos de manera visual
- **Tesis y proyectos**: Desarrolla presentaciones académicas profesionales
- **Capacitación**: Material educativo para estudiantes

### Para Desarrolladores
- **Documentación técnica**: Presenta arquitecturas y flujos de trabajo
- **Demos de productos**: Muestra funcionalidades de software
- **Reportes de progreso**: Actualiza stakeholders sobre avances
- **Propuestas técnicas**: Presenta soluciones a problemas complejos

## 🔧 API REST - Generar Presentaciones

### Generar Presentación

**Endpoint:** `/api/v1/ppt/presentation/generate`
**Método:** `POST`
**Content-Type:** `application/json`

#### Parámetros de la Solicitud

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| content | string | Sí | El contenido para generar la presentación |
| slides_markdown | string[] \| null | No | El markdown para las diapositivas |
| instructions | string \| null | No | Instrucciones para generar la presentación |
| tone | string | No | Tono del texto (por defecto: "default"). Opciones: "default", "casual", "professional", "funny", "educational", "sales_pitch" |
| verbosity | string | No | Nivel de detalle del texto (por defecto: "standard"). Opciones: "concise", "standard", "text-heavy" |
| web_search | boolean | No | Habilitar búsqueda web (por defecto: false) |
| n_slides | integer | No | Número de diapositivas (por defecto: 8) |
| language | string | No | Idioma de la presentación (por defecto: "English") |
| template | string | No | Plantilla a usar (por defecto: "general") |
| include_table_of_contents | boolean | No | Incluir tabla de contenidos (por defecto: false) |
| include_title_slide | boolean | No | Incluir diapositiva de título (por defecto: true) |
| files | string[] \| null | No | Archivos para la presentación |
| export_as | string | No | Formato de exportación (por defecto: "pptx"). Opciones: "pptx", "pdf" |

#### Ejemplo de Solicitud

```bash
curl -X POST http://localhost:5000/api/v1/ppt/presentation/generate \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Introducción al Aprendizaje Automático",
    "n_slides": 5,
    "language": "Spanish (Español)",
    "template": "general",
    "export_as": "pptx"
  }'
```

#### Respuesta de Ejemplo

```json
{
  "presentation_id": "d3000f96-096c-4768-b67b-e99aed029b57",
  "path": "/app_data/d3000f96-096c-4768-b67b-e99aed029b57/Introduccion_al_Aprendizaje_Automatico.pptx",
  "edit_path": "/presentation?id=d3000f96-096c-4768-b67b-e99aed029b57"
}
```

Para información detallada, consulta la [documentación de la API](https://docs.presenton.ai/using-presenton-api).

## 🎨 Características de la Interfaz de Usuario

### 1. Agregar prompt, seleccionar número de diapositivas e idioma
![Demo](readme_assets/images/prompting.png)

### 2. Seleccionar tema
![Demo](readme_assets/images/select-theme.png)

### 3. Revisar y editar esquema
![Demo](readme_assets/images/outline.png)

### 4. Presentar en la aplicación
![Demo](readme_assets/images/present.png)

### 5. Cambiar tema
![Demo](readme_assets/images/change-theme.png)

### 6. Exportar presentación como PDF y PPTX
![Demo](readme_assets/images/export-presentation.png)

## 🗺️ Hoja de Ruta

- [x] Soporte para plantillas HTML personalizadas por desarrolladores
- [x] Soporte para acceder a plantillas personalizadas a través de API
- [x] Implementar servidor MCP
- [ ] Capacidad para que los usuarios cambien el prompt del sistema
- [x] Soporte para base de datos SQL externa

## 🤝 Comunidad

Únete a nuestra comunidad para obtener soporte, compartir ideas y contribuir:

- **Discord**: [https://discord.gg/9ZsKKxudNE](https://discord.gg/9ZsKKxudNE)
- **X (Twitter)**: [@presentonai](https://x.com/presentonai)
- **Documentación**: [https://docs.presenton.ai](https://docs.presenton.ai)

## 🔧 Solución de Problemas

### Problemas Comunes

1. **Error de conexión con Ollama**
   - Asegúrate de que Ollama esté ejecutándose
   - Verifica la URL de Ollama en las variables de entorno

2. **Problemas con claves API**
   - Verifica que las claves API sean válidas
   - Asegúrate de tener créditos suficientes en tu cuenta

3. **Errores de Docker**
   - Asegúrate de tener Docker instalado y ejecutándose
   - Verifica que el puerto 5000 esté disponible

4. **Problemas de memoria con GPU**
   - Reduce el tamaño del modelo Ollama
   - Verifica la memoria GPU disponible

### Logs y Depuración

Para ver los logs detallados:
```bash
docker logs presenton
```

Para ejecutar en modo desarrollo con logs detallados:
```bash
docker-compose up development
```

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia Apache 2.0. Consulta el archivo [LICENSE](LICENSE) para más detalles.

## 🙏 Contribuciones

¡Las contribuciones son bienvenidas! Por favor:

1. Haz fork del repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📞 Soporte

Para soporte técnico y consultas:

- **Email**: [suraj@presenton.ai](mailto:suraj@presenton.ai)
- **Discord**: [Comunidad de Presenton](https://discord.gg/9ZsKKxudNE)
- **Documentación**: [docs.presenton.ai](https://docs.presenton.ai)

---

**¿Te gusta Presenton?** ¡Dale una ⭐ estrella en GitHub para mostrar tu apoyo!