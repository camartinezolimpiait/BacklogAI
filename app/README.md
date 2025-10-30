

# Documentación Técnica — Submódulo `app/` de EcoMarket-RAG

---

## 1. Estructura del submódulo `app/`

```
app/
├── api/           # Endpoints FastAPI, lógica de devoluciones y herramientas para el agente
├── config/        # settings.py (Pydantic, variables de entorno)
├── front/         # SPA Gradio y HTML (chat UI)
├── langchain/     # Orquestación de agentes y herramientas (LangChain/LangGraph)
├── rag/           # Embeddings, retrieval, generator, prompts
├── README.md      # Este archivo
└── __init__.py
```

---

## 2. Componentes y responsabilidades

- **api/**
	- `apiFast.py`: Endpoints REST (pedidos, devoluciones, consulta RAG, health, etc.)
	- `apiFast_tools.py`: Herramientas BaseTool para integración con agentes LangChain/LangGraph
	- `devoluciones.py`: Lógica de devoluciones y elegibilidad

- **config/**
	- `settings.py`: Configuración centralizada vía Pydantic, carga de variables de entorno

- **front/**
	- `grad.py`: SPA Gradio (chatbot UI, integración con agente y retrieval)
	- `index.html`: SPA HTML alternativa (estilos y estructura de chat)

- **langchain/**
	- `lang.py`: Orquestación de agentes, integración con herramientas, configuración de tracing LangSmith

- **rag/**
	- `embeddings.py`, `embeddings_hugging_face.py`: Generación de embeddings (HuggingFace, OpenAI, Azure)
	- `retriever.py`: Recuperación semántica y chunking de documentos
	- `generator.py`: Generación de respuestas con contexto
	- `prompts.txt`: Plantillas de prompts para el LLM

---

## 3. Flujo de ejecución y arquitectura

1. **Ingesta**: Documentos PDF locales o desde Azure Blob Storage → chunking → embeddings → indexación en ChromaDB
2. **Consulta**: Usuario envía pregunta vía SPA (Gradio) o API REST → embeddings de la consulta → retrieval top-k en ChromaDB → LLM genera respuesta con contexto y citas
3. **Devoluciones**: Endpoints y lógica para registrar y verificar devoluciones de pedidos
4. **Observabilidad**: Logs avanzados (Loguru) y tracing opcional con LangSmith

**Diagrama simplificado:**
```
Usuario (Gradio/HTML) ──> FastAPI ──> LangChain/LangGraph ──> ChromaDB ──> LLM/Embeddings
				 ▲                        │
				 └─────────────<──────────┘
```

---

## 4. Configuración y uso

1. Instala dependencias desde la raíz:
	 ```bash
	 pip install -r requirements.txt
	 ```
2. Configura el archivo `.env` en la raíz con tus credenciales y parámetros (ver README principal).
3. Ejecuta el sistema desde la raíz:
	 ```bash
	 python main.py
	 ```
	 - FastAPI: http://localhost:8000/docs
	 - Gradio: http://localhost:7000

---

## 5. Ejemplo de endpoints y uso

- `GET /health` — Estado del sistema
- `GET /get_orders_dataset` — Dataset de órdenes
- `GET /get_order?orden_servicio=...` — Detalles de una orden
- `POST /query` — Consulta RAG (body: query, top_k, temperature)
- `POST /register_return_order` — Registrar devolución
- `POST /verify_eligibility_order` — Verificar elegibilidad de devolución

---

## 6. Notas técnicas

- El submódulo `app/` es autocontenible y puede ser probado de forma aislada usando los tests en `../tests/`.
- El frontend Gradio puede personalizarse fácilmente editando `front/grad.py` y los estilos de `index.html`.
- El tracing de agentes (LangSmith) se configura vía variables de entorno y es opcional.

---

## 7. Créditos

Desarrollado para la Maestría en IA Aplicada, Universidad Icesi.

---

## 5. Extensión y Personalización

- Puedes agregar nuevos loaders en `rag/` para otros formatos de documentos.
- Modifica los prompts en `prompts.txt` para adaptar el estilo conversacional.
- Cambia el modelo de embeddings en `embeddings_hugging_face.py` según tus necesidades.

---

## 6. Buenas Prácticas

- Mantén las dependencias actualizadas y revisa el archivo `requirements.txt`.
- Protege las claves API y configura los permisos de acceso.
- Versiona los documentos y realiza pruebas unitarias con cada cambio.

---

Para más detalles, consulta el README principal del proyecto o la carpeta `docs/`.
