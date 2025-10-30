from fastapi import Request

# ...existing code...

from fastapi import Body

#!/usr/bin/env python3
"""
EcoMarket RAG Solution - FastAPI API
"""

from fastapi import FastAPI, HTTPException, Depends, Query as FastAPIQuery
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from loguru import logger
from contextlib import asynccontextmanager
import httpx
import os

from app.rag.embeddings import EmbeddingService
from app.rag.retriever import DocumentRetriever
from app.rag.generator import ResponseGenerator
from app.api.devoluciones import DevolutionsGenerator
from app.config.settings import get_settings

logger.info("Logging initialized")

embedding_service = None
retriever = None
generator = None
devolutions = None	

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(default=3, ge=1, le=10)
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)

class QueryResponse(BaseModel):
    answer: str
    sources: list[dict]
    confidence: float

class OrderResponse(BaseModel):
    tracking_number: int
    order_id: str
    customer_name: str
    city: str
    product: str
    category: str
    status: str
    carrier: str
    track_url: str
    notes: str
    delayed: bool
    eta: str
    last_update: str

# Modelo para registrar devolución
class RegistrarDevolucionRequest(BaseModel):
    codigo_devolucion: str

# Respuesta para registro de devolución
class RegistrarDevolucionResponse(BaseModel):
    success: bool
    message: str
 
class VerifyEligibilityRequest(BaseModel):
    orden_servicio: str

class VerifyEligibilityResponse(BaseModel):
    elegible: bool
    motivo: str
    
@asynccontextmanager
async def lifespan(app: FastAPI):
    global embedding_service, retriever, generator, devolutions
    logger.info("Initializing EcoMarket RAG application...")
    settings = get_settings()
    embedding_service = EmbeddingService()
    retriever = DocumentRetriever(embedding_service)
    generator = ResponseGenerator()
    devolutions = DevolutionsGenerator()

    # Descargar dataset de órdenes y guardarlo en settings.rows_dataset
    import asyncio
    import httpx
    async def fetch_orders_dataset():
        async with httpx.AsyncClient() as client:
            response = await client.get(settings.endpointdataset)
            data = response.json()
            return data.get("rows", [])
    try:
        settings.rows_dataset = await fetch_orders_dataset()
        logger.info(f"Dataset de órdenes cargado: {len(settings.rows_dataset)} filas")
    except Exception as e:
        logger.error(f"Error al cargar dataset de órdenes: {e}")
        settings.rows_dataset = []

    logger.info("Application initialized successfully")
    yield
    logger.info("Shutting down application...")

app = FastAPI(
    title="EcoMarket RAG API",
    description="RAG-based product information and recommendation system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "healthy", "service": "EcoMarket RAG API"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "embedding_service": embedding_service is not None,
        "retriever": retriever is not None,
        "generator": generator is not None,
        "devolutions": devolutions is not None
    }

@app.get("/get_orders_dataset")
async def get_orders_dataset():
    settings = get_settings()
    if settings.rows_dataset is not None:
        return settings.rows_dataset
    else:
        return []

@app.get("/get_order", response_model=OrderResponse)
async def get_order(orden_servicio: str = FastAPIQuery(..., min_length=14, max_length=15)):
    import re
    if not orden_servicio or not re.match(r"^[A-Z]{3}-\d{4}-\d{5}$", orden_servicio):
        raise HTTPException(status_code=400, detail="El parámetro 'orden_servicio' es obligatorio y debe tener el formato correcto (ECO-2509-20001)")

    settings = get_settings()
    rows = settings.rows_dataset if settings.rows_dataset is not None else []

    # Buscar la orden por order_id
    order = next((row for row in rows if row['row']['order_id'] == orden_servicio), None)
    if not order:
        return OrderResponse(
            tracking_number=0,
            order_id=orden_servicio,
            customer_name="",
            city="",
            product=f"No se encontró la orden de servicio: {orden_servicio}",
            category="",
            status="",
            carrier="",
            track_url="",
            notes="",
            delayed=False,
            eta="",
            last_update=""
        )

    # Retornar objeto OrderResponse con los datos encontrados
    return OrderResponse(
        tracking_number=order['row'].get('tracking_number', 0),
        order_id=order['row'].get('order_id', orden_servicio),
        customer_name=order['row'].get("customer_name", ""),
        city=order['row'].get("city", ""),
        product=order['row'].get("product", ""),
        category=order['row'].get("category", ""),
        status=order['row'].get("status", ""),
        carrier=order['row'].get("carrier", ""),
        track_url=order['row'].get("track_url", ""),
        notes=order['row'].get("notes", ""),
        delayed=order['row'].get("delayed", False),
        eta=order['row'].get("eta", ""),
        last_update=order['row'].get("last_update", "")
    )

@app.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    import re
    try:
        logger.info(f"Processing query: {request.query}")
        # Buscar el patrón en cualquier parte del texto
        match = re.search(r"[A-Z]{3}-\d{4}-\d{5}", request.query)
        orden_servicio = match.group(0) if match else None
        logger.info(f"Orden de servicio detectada: {orden_servicio}")
     
        if orden_servicio:
            info_order = await get_order(orden_servicio)
            new_query = f"{request.query}\nDetalles de la orden de servicio:" \
                        f"ID: {info_order.order_id} " \
                        f"Cliente: {info_order.customer_name} " \
                        f"Ciudad: {info_order.city} " \
                        f"Producto: {info_order.category} {info_order.product} " \
                        f"Tipo de producto: {info_order.category} " \
                        f"Estado: {info_order.status} " \
                        f"Transportista: {info_order.carrier} " \
                        f"URL de seguimiento: {info_order.track_url} " \
                        f"Notas: {info_order.notes} " \
                        f"Retraso: {info_order.delayed} " \
                        f"ETA: {info_order.eta} " \
                        f"Última actualización: {info_order.last_update} "
        else:
            new_query = request.query
   
        logger.info(f"Información de la orden: {new_query}")
        documents = await retriever.retrieve(
            new_query,
            top_k=request.top_k
        )
  
        response = await generator.generate(
            query=new_query,
            documents=documents,
            temperature=request.temperature
        )

        return QueryResponse(
            answer=response["answer"],
            sources=response["sources"],
            confidence=response["confidence"]
        )
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/register_return_order", response_model=RegistrarDevolucionResponse)
async def registrar_orden_devolucion(request: RegistrarDevolucionRequest = Body(...)):
    import re
    import random
    
    codigo = request.codigo_devolucion
    
    match = re.search(r"[A-Z]{3}-\d{4}-\d{5}-\d{6}", codigo)
    orden_devolucion = match.group(0) if match else None
    if not orden_devolucion:
        match_orden_servicio = re.search(r"[A-Z]{3}-\d{4}-\d{5}", codigo)
        if match_orden_servicio:
            orden_devolucion = match_orden_servicio.group(0)
            random_number = random.randint(100000, 999999)
            orden_devolucion = f"{orden_devolucion}-{random_number}"
        else:
            return False
    
    match_orden_servicio = re.search(r"[A-Z]{3}-\d{4}-\d{5}", orden_devolucion)
    orden_servicio = match_orden_servicio.group(0) if match_orden_servicio else None
    if not orden_servicio:
        return False

    await devolutions.registrar_devolucion_en_json(orden_devolucion)
    return RegistrarDevolucionResponse(success=True, message=f"Devolución registrada correctamente: {orden_devolucion}")

@app.post("/verify_eligibility_order", response_model=VerifyEligibilityResponse)
async def verify_eligibility_order(request: VerifyEligibilityRequest):
    import re
    orden_servicio = request.orden_servicio
    if not orden_servicio or not re.match(r"^[A-Z]{3}-\d{4}-\d{5}$", orden_servicio):
        return VerifyEligibilityResponse(elegible=False, motivo="Formato de orden de servicio inválido.")
    settings = get_settings()
    rows = settings.rows_dataset if settings.rows_dataset is not None else []
    order = next((row['row'] for row in rows if row['row']['order_id'] == orden_servicio), None)
    if not order:
        return VerifyEligibilityResponse(elegible=False, motivo="Orden de servicio no encontrada.")
    elegible, motivo = await devolutions.is_eligible_for_return(order)
    return VerifyEligibilityResponse(elegible=elegible, motivo=motivo)

@app.post("/verify_eligibility_order_response", response_model=VerifyEligibilityResponse)
async def verify_eligibility_order_response(request: VerifyEligibilityRequest):
    import re
    orden_servicio = request.orden_servicio
    match = re.search(r"[A-Z]{3}-\d{4}-\d{5}-\d{6}", orden_servicio)
    orden_devolucion = match.group(0) if match else None
    if not orden_devolucion:
        match_orden_servicio = re.search(r"[A-Z]{3}-\d{4}-\d{5}", orden_servicio)
        orden_servicio = match_orden_servicio.group(0) if match_orden_servicio else None
        
    if not orden_servicio or not re.match(r"^[A-Z]{3}-\d{4}-\d{5}$", orden_servicio):
        return VerifyEligibilityResponse(elegible=False, motivo="Formato de orden de servicio inválido.")

    return VerifyEligibilityResponse(elegible=True, motivo="Elegible para devolución")