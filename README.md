
# EcoMarket-RAG

Solución de Recuperación Aumentada por Generación (RAG) para consultas inteligentes sobre pedidos, devoluciones y documentos en el dominio EcoMarket. Incluye backend FastAPI, frontend SPA (Gradio/HTML), integración con LangChain, ChromaDB, Azure Blob Storage y observabilidad con LangSmith.

---

## Autores
- Carlos Alberto Martinez Ramirez
- Wilman Andres Quiñonez Valencia

---

## Arquitectura General

**Componentes:**
- **FastAPI**: API REST para consultas, pedidos y devoluciones.
- **LangChain/LangGraph**: Orquestación de agentes, herramientas y flujos RAG.
- **ChromaDB**: Vector store local para embeddings y búsqueda semántica.
- **Azure Blob Storage**: Almacenamiento de PDFs y dataset de órdenes.
- **OpenAI/Azure OpenAI/Hugging Face**: Modelos LLM y embeddings.
- **Gradio**: SPA frontend tipo chat.
- **Loguru**: Logging avanzado.
- **LangSmith**: Observabilidad y tracing de agentes.

**Flujo principal:**
1. Usuario interactúa vía SPA (Gradio) o API REST.
2. FastAPI recibe la consulta, valida, enruta a RAG y gestiona devoluciones.
3. LangChain/LangGraph orquesta: embeddings, retrieval (ChromaDB), contexto y prompt.
4. LLM genera respuesta citando fuentes.
5. Respuesta y estado de devoluciones se retornan al usuario.

**Diagrama:**
```
Usuario [(SPA/Gradio) ── FastAPI] ──> LangChain/LangGraph ──> ChromaDB ──> LLM/Embeddings
         ▲                        │
         └─────────────<──────────┘
```

---

## Estructura del Proyecto

```
EcoMarket-RAG/
├── main.py                # Entry point: lanza FastAPI y Gradio simultáneamente
├── requirements.txt       # Dependencias
├── .env                   # Configuración y credenciales
├── app/
│   ├── api/               # Endpoints FastAPI, Tools LangChain y lógica de devoluciones
│   ├── config/            # settings.py (Pydantic, variables de entorno)
│   ├── front/             # SPA Gradio y HTML
│   ├── langchain/         # Orquestación de agentes y herramientas
│   └── rag/               # Embeddings, retrieval, generator, prompts
├── tests/                 # Pruebas unitarias
└── docs/                  # Documentos y dataset
```

---

## Configuración y Variables de Entorno

1. Copia `.env.example` a `.env` y completa:
   - Claves de Azure OpenAI, Blob Storage, etc.
   - Parámetros de LangSmith para tracing (opcional):
     ```env
     LANGCHAIN_TRACING_V2=true
     LANGCHAIN_API_KEY=tu_api_key
     LANGCHAIN_PROJECT=openai_tracing_ecomarket
     ```
2. El archivo `.env` es leído automáticamente por `settings.py`.

---

## Instalación y Ejecución

1. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   ```
2. Ejecuta el sistema (API y frontend Gradio en paralelo):
   ```bash
   python main.py
   ```
   - FastAPI: http://localhost:8000/docs
   - Gradio: http://localhost:7000

---

## Endpoints Principales (FastAPI)

- `GET /health` — Estado del sistema
- `GET /get_orders_dataset` — Dataset de órdenes
- `GET /get_order?orden_servicio=...` — Detalles de una orden
- `POST /query` — Consulta RAG (body: query, top_k, temperature)
- `POST /register_return_order` — Registrar devolución
- `POST /verify_eligibility_order` — Verificar elegibilidad de devolución

---

## Frontend SPA (Gradio)

- Interfaz de chat moderna (ver `app/front/grad.py` y `index.html`)
- Permite consultas naturales, seguimiento de pedidos y devoluciones

---

## Observabilidad y Tracing

- Soporte para LangSmith/LangChain Tracing (configurable vía `.env`)
- Logs avanzados con Loguru

---

## Pruebas

```bash
pytest tests/
```

---

## Créditos

Proyecto académico — Maestría en IA Aplicada, Universidad Icesi

### 5. Pruebas unitarias
```bash
pytest
```

## Stack Técnico
- **Lenguaje:** Python 3.10+
- **API:** FastAPI
- **Orquestación RAG:** LangChain
- **Frontend:** Gradio (SPA)
- **Monitoreo:** LangSmith (opcional)
- **Vector DB:** ChromaDB (local)
- **Almacenamiento:** Azure Blob Storage (opcional)
- **LLMs/Embeddings:** OpenAI, Azure OpenAI, Hugging Face Transformers
- **Testing:** pytest, pytest-asyncio
- **Logging:** loguru

## Dependencias principales
- fastapi
- uvicorn
- loguru
- pydantic
- torch==2.3.0
- torchvision==0.18.0
- transformers==4.38.2
- sentence-transformers
- azure-ai-inference
- pypdf
- azure-storage-blob
- chromadb
- openai
- langsmith
- langchain>=0.3
- langchain-core>=0.3.78,<1.0.0
- langchain-community>=0.3
- langchain-openai>=0.3.35
- langchain-text-splitters>=0.3.11
- langgraph>=1.0.0
- langgraph-checkpoint>=3.0.0
- langgraph-prebuilt>=1.0.0
- pydantic>=2
- gradio

### Dependencias de soporte (testing y logging)
- pytest
- pytest-asyncio
- requests
- structlog (opcional)

Consulta el archivo `requirements.txt` para versiones exactas y dependencias adicionales.

## Notas y recomendaciones
- Para ingestar documentos desde Azure Blob Storage, configura correctamente las variables de conexión en `.env` y usa el método `load_and_index_pdfs_from_blob`.
- Puedes personalizar el modelo de embeddings usando Hugging Face (`EmbeddingHuggingFaceService`) o Sentence Transformers.
- La arquitectura permite extender el vector store a Pinecone, Qdrant, etc. para producción.
- Revisa los logs en la carpeta `logs/` para trazabilidad y debugging.

---


## Ejemplo de Ejecución

1. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   ```
2. Configura `.env` con tus claves y parámetros.
3. Ejecuta la API:
   ```bash
   python main.py
   ```
4. Accede a la documentación interactiva en `http://localhost:8000/docs`.
5. Realiza consultas usando el endpoint `/query`.

### Ejemplo de consulta con `curl`:
```plaintext
curl -X 'POST' \
  'http://127.0.0.1:8000/query' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "query": "¿Que leyes cumple ecomarket para protejer a sus compradores?",
  "top_k": 3,
  "temperature": 0.7
}'

{
  "answer": "Soy el Asistente de Servicio al Cliente. Estoy aquí para informarte sobre nuestra tienda y ayudarte con cualquier otra consulta relacionada con nuestras políticas.\n\nEcoMarket cumple con varias leyes colombianas para proteger a sus compradores y garantizar una experiencia de compra segura y transparente. Entre estas leyes se encuentran:\n\n- Ley 1480 de 2011 – Estatuto del Consumidor Colombiano, que protege los derechos de los consumidores.\n- Ley 527 de 1999 – Comercio electrónico y firmas digitales, que regula las transacciones electrónicas.\n- Ley 1581 de 2012 – Protección de datos personales, que salvaguarda la privacidad de los clientes.\n- Decreto 1074 de 2015 – Decreto Único Reglamentario del Sector Comercio, Industria y Turismo, que establece normativas aplicables al comercio.\n\nEstas normativas respaldan nuestro compromiso con la transparencia, la satisfacción del cliente y el comercio responsable.\n\nFue un gusto proporcionarle la información solicitada, no dude en volver a usar nuestros servicios de Chat Autómatizado. Cordialmente: Servicio al Cliente",
  "sources": [
    {
      "content": "solución conciliada basada en buena fe y comunicación transparente. \nPolítica de compra a proveedores19. Las muestras de producto, cuando sean requeridas, \ndeberán ser proporcionadas sin costo por el ",
      "metadata": {
        "filename": "Politicas_Compra_Proveedores_EcoMarket.pdf",
        "chunk": 5
      }
    },
    {
      "content": "EcoMarket reafirma su compromiso con la transparencia, la satisfacción del cliente y el \ncomercio responsable. Estas políticas buscan asegurar una experiencia de compra con fiable \ny coherente con los",
      "metadata": {
        "filename": "Politicas_Compra_Cliente_EcoMarket.pdf",
        "chunk": 6
      }
    },
    {
      "content": "Políticas de Compra a Proveedores – EcoMarket \nDatos General \nTítulo: Políticas de Compra a Proveedores – EcoMarket \nAutor: Departamento de Abastecimiento y Compras Sostenibles \nFecha: 11/10/2025 \n \nD",
      "metadata": {
        "filename": "Politicas_Compra_Proveedores_EcoMarket.pdf",
        "chunk": 0
      }
    }
  ],
  "confidence": 0.3709913889567057
}
```  
---
Para dudas, revisa la documentación en la carpeta `docs/` o contacta al equipo de EcoMarket.