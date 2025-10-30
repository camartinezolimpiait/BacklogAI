from langchain.tools import BaseTool
from typing import Optional
import requests

class GetOrdersDatasetTool(BaseTool):
    name: str = "get_orders_dataset"
    description: str = "Obtiene el dataset de órdenes de servicio registradas. No requiere parámetros."

    def _run(self) -> list:
        from app.config.settings import get_settings
        settings = get_settings()
        return settings.rows_dataset or []

    async def _arun(self) -> list:
        raise NotImplementedError("Async not implemented")

class GetOrderTool(BaseTool):
    name: str = "get_order"
    description: str = "Obtiene los detalles de una orden de servicio por su código. Input: orden_servicio (str)"

    def _run(self, orden_servicio: str) -> dict:
        import re
        from app.config.settings import get_settings
        from app.api.devoluciones import DevolutionsGenerator
        settings = get_settings()
        rows = settings.rows_dataset or []
        if not orden_servicio or not re.match(r"^[A-Z]{3}-\d{4}-\d{5}$", orden_servicio):
            return {"error": "Formato de orden de servicio inválido."}
        order = next((row['row'] for row in rows if row['row']['order_id'] == orden_servicio), None)
        if not order:
            return {"error": f"No se encontró la orden de servicio: {orden_servicio}"}

        devolucion = DevolutionsGenerator().buscar_devolucion(orden_servicio)
        if devolucion:
            return {"error": f"La orden de servicio {orden_servicio} tiene una devolución registrada."}
        return order

    async def _arun(self, orden_servicio: str) -> dict:
        raise NotImplementedError("Async not implemented")

class QueryRAGTool(BaseTool):
    name: str = "query_rag"
    description: str = "Realiza una consulta RAG y devuelve la respuesta generada. Input: query (str), top_k (int, opcional), temperature (float, opcional)"

    def _run(self, query: str, top_k: Optional[int] = 3, temperature: Optional[float] = 0.7) -> dict:
        from app.api.apiFast import retriever, generator
        try:
            documents = retriever.retrieve(query, top_k=top_k)
            response = generator.generate(query=query, documents=documents, temperature=temperature)
            return response
        except Exception as e:
            return {"error": str(e)}

    async def _arun(self, query: str, top_k: Optional[int] = 3, temperature: Optional[float] = 0.7) -> dict:
        raise NotImplementedError("Async not implemented")

class RegisterReturnOrderTool(BaseTool):
    name: str = "register_return_order"
    description: str = "Registra una devolución para una orden. Input: codigo_devolucion (str)"

    def _run(self, codigo_devolucion: str) -> dict:
        from app.api.apiFast import devolutions
        try:
            result: str = devolutions.registrar_devolucion(codigo_devolucion)
            return {"success": True, "message": f"Devolución registrada: {result}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _arun(self, codigo_devolucion: str) -> dict:
        raise NotImplementedError("Async not implemented")

class VerifyEligibilityOrderTool(BaseTool):
    name: str = "verify_eligibility_order"
    description: str = "Verifica si una orden es elegible para devolución. Input: orden_servicio (str)"

    def _run(self, orden_servicio: str) -> dict:
        from app.api.apiFast import devolutions
        from app.config.settings import get_settings
        import re
        settings = get_settings()
        rows = settings.rows_dataset or []
        if not orden_servicio or not re.match(r"^[A-Z]{3}-\d{4}-\d{5}$", orden_servicio):
            return {"elegible": False, "motivo": "Formato de orden de servicio inválido."}
        order = next((row['row'] for row in rows if row['row']['order_id'] == orden_servicio), None)
        if not order:
            return {"elegible": False, "motivo": "Orden de servicio no encontrada."}
        
        # Regla 5: Productos no elegibles por tipo
        tipo = order.get("category", "").lower()
        if any(palabra in tipo for palabra in ["higiene", "cosméticos", "alimentos", "bebidas"]):
            return {"elegible": False, "motivo": "Productos de higiene personal, cosméticos, alimentos o bebidas no pueden ser devueltos."}
        # Regla 6: Status debe ser 'Entregado'
        status = order.get("status", "")
        if status.strip().lower() != "entregado":
            return {"elegible": False, "motivo": "Solo productos con status 'Entregado' pueden ser devueltos."}
        return {"elegible": True, "motivo": "Elegible para devolución."}

       

    async def _arun(self, orden_servicio: str) -> dict:
        raise NotImplementedError("Async not implemented")
