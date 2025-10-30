import os
import json
import re
from pathlib import Path
from glob import glob
from loguru import logger
import httpx
from app.config.settings import get_settings
from pydantic import BaseModel, Field

class OrderResponse(BaseModel):
    tracking_number: int = Field(..., description="Número de seguimiento del pedido")
    order_id: str = Field(..., description="ID de la orden de servicio")
    customer_name: str = Field(..., description="Nombre del cliente")
    city: str = Field(..., description="Ciudad del cliente")
    product: str = Field(..., description="Nombre del producto")
    category: str = Field(..., description="Categoría del producto")
    status: str = Field(..., description="Estado del pedido")
    carrier: str = Field(..., description="Nombre del transportista")
    track_url: str = Field(..., description="URL para rastrear el pedido")
    notes: str = Field(..., description="Notas adicionales sobre el pedido")
    delayed: bool = Field(..., description="Indica si el pedido está retrasado")
    eta: str = Field(..., description="Fecha estimada de entrega")
    last_update: str = Field(..., description="Última actualización del estado del pedido")
    devolution_code: str = Field(..., description="Código de devolución asociado a la orden")
 
class DevolutionsGenerator:
    """
        DevolutionsGenerator
    A class responsible for managing product return (devolution) operations within the application.
    This class provides methods to:
    - Search for existing devolutions by service order ID.
    - Register new devolutions in JSON files, validating codes and updating all relevant datasets.
    - Determine if an order is eligible for return based on its category and delivery status.
    Methods
    -------
    __init__():
        Initializes the DevolutionsGenerator instance and loads application settings.
    async buscar_devolucion_por_orden(orden_servicio: str) -> bool:
        Checks if a devolution is registered for a specific service order ID by searching a JSON file.
    async registrar_devolucion_en_json(codigo_devolucion: str) -> bool:
        Registers a devolution in all JSON files in the 'docs' folder, validating the code format and associating it with an order.
    async is_eligible_for_return(order_row: dict) -> tuple[bool, str]:
        Determines if an order item is eligible for return based on its category and delivery status.
    Notes
    -----
    - Devolutions are stored in JSON files located in the 'docs' directory of the project.
    - The class relies on external configuration and remote datasets for order validation.
    """
    def __init__(self):
        """Initialize the DevolutionsGenerator"""
        logger.info("Initializing DevolutionsGenerator")
        settings = get_settings()


    async def buscar_devolucion_por_orden(self, orden_servicio: str) -> bool:
        """
        Busca si existe una devolución registrada para una orden de servicio específica.

        Args:
            orden_servicio (str): El ID de la orden de servicio a buscar.

        Returns:
            bool: True si se encuentra una devolución para la orden de servicio dada, False en caso contrario.

        Notas:
            - Busca en el archivo 'devoluciones_registradas.json' ubicado en la carpeta 'docs' del proyecto.
            - Si el archivo no existe, está vacío o ocurre un error al cargar el JSON, retorna False.
        """
        docs_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "docs")
        json_path = os.path.join(docs_folder, "devoluciones_registradas.json")
        if not os.path.exists(json_path):
            return False
        with open(json_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return False
            try:
                data = json.loads(content)
            except Exception:
                logger.error("Error al cargar el archivo JSON de devoluciones")
                return False
            for registro in data:
                if registro.get("order_id") == orden_servicio:
                    return True
            return False

    def buscar_devolucion(self, orden_servicio: str) -> bool:
            """
            Busca si existe una devolución registrada para una orden de servicio específica.

            Args:
                orden_servicio (str): El ID de la orden de servicio a buscar.

            Returns:
                bool: True si se encuentra una devolución para la orden de servicio dada, False en caso contrario.

            Notas:
                - Busca en el archivo 'devoluciones_registradas.json' ubicado en la carpeta 'docs' del proyecto.
                - Si el archivo no existe, está vacío o ocurre un error al cargar el JSON, retorna False.
            """
            docs_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "docs")
            json_path = os.path.join(docs_folder, "devoluciones_registradas.json")
            if not os.path.exists(json_path):
                return False
            with open(json_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return False
                try:
                    data = json.loads(content)
                except Exception:
                    logger.error("Error al cargar el archivo JSON de devoluciones")
                    return False
                for registro in data:
                    if registro.get("order_id") == orden_servicio:
                        return True
                return False


    async def registrar_devolucion_en_json(self, codigo_devolucion: str) -> bool:
        """
        Registra una devolución en los archivos JSON correspondientes dado un código de devolución.
        Este método valida el formato del código de devolución, busca la orden asociada en un dataset remoto,
        y si la encuentra, agrega la información de la devolución en todos los archivos JSON ubicados en la carpeta 'docs'.
        Args:
            codigo_devolucion (str): Código de devolución a registrar. Debe tener el formato 'AAA-0000-00000-000000'.
        Returns:
            bool: True si la devolución fue registrada exitosamente en los archivos JSON, False en caso contrario.
        """
        import re
        import json
        import httpx
        import os
        from pathlib import Path
        from glob import glob
        from app.config.settings import get_settings
        
        codigo = codigo_devolucion
                
        match = re.search(r"[A-Z]{3}-\d{4}-\d{5}-\d{6}", codigo)
        etiqueta_devolucion = match.group(0) if match else None
        if not etiqueta_devolucion:
            return False

        # Obtener dataset de órdenes
        with httpx.Client() as client:
            settings = get_settings()
            response = client.get(settings.endpointdataset)
            data = response.json()
            rows = data.get("rows", [])

        match_orden_servicio = re.search(r"[A-Z]{3}-\d{4}-\d{5}", etiqueta_devolucion)
        orden_servicio = match_orden_servicio.group(0) if match_orden_servicio else None
        if not orden_servicio:
            return False
        # Buscar la orden por order_id
        order = next((row for row in rows if row['row']['order_id'] == orden_servicio), None)

        if order:
            order_response = OrderResponse(
                tracking_number=order['row'].get('tracking_number', 0),
                order_id=order['row'].get('order_id', orden_servicio),
                customer_name=order['row'].get("customer_name", ""),
                city=order['row'].get("city", ""),
                product=order['row'].get("product", ""),
                category=order['row'].get("category", ""),
                status=order['row'].get("status", ""),
                carrier=order['row'].get("carrier", ""),
                track_url=order['row'].get("track_url", ""),
                notes=order['row'].get("notes", "") + f" Devolución registrada con código: {etiqueta_devolucion}",
                delayed=order['row'].get("delayed", False),
                eta=order['row'].get("eta", ""),
                last_update=order['row'].get("last_update", ""),
                devolution_code=etiqueta_devolucion
            )

            docs_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "docs")
            json_files = glob(os.path.join(docs_folder, "*.json"))
            try:
                for json_path in json_files:
                    try:
                        with open(json_path, "r", encoding="utf-8") as f:
                            content = f.read().strip()
                            if not content:
                                json_data = []
                            else:
                                json_data = json.loads(content)
                        json_data.append(order_response.dict())
                        with open(json_path, "w", encoding="utf-8") as f:
                            json.dump(json_data, f, ensure_ascii=False, indent=2)
                    except Exception:
                        return False
            except Exception:
                logger.error(f"Error al registrar la devolución en los archivos JSON.")
                return False
            return True
        else:
            return False
    
    def registrar_devolucion(self, codigo_devolucion: str) -> str:
        """
        Registra una devolución en los archivos JSON correspondientes dado un código de devolución.
        Este método valida el formato del código de devolución, busca la orden asociada en un dataset remoto,
        y si la encuentra, agrega la información de la devolución en todos los archivos JSON ubicados en la carpeta 'docs'.
        Args:
            codigo_devolucion (str): Código de devolución a registrar. Debe tener el formato 'AAA-0000-00000'.
        Returns:
            bool: True si la devolución fue registrada exitosamente en los archivos JSON, False en caso contrario.
        """
        import re
        import json
        import httpx
        import os
        from pathlib import Path
        from glob import glob
        from app.config.settings import get_settings
        import random

        codigo = codigo_devolucion

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

        # Obtener dataset de órdenes
        with httpx.Client() as client:
            settings = get_settings()
            response = client.get(settings.endpointdataset)
            data = response.json()
            rows = data.get("rows", [])

        # Buscar la orden por order_id
        order = next((row for row in rows if row['row']['order_id'] == orden_servicio), None)

        if order:
            order_response = OrderResponse(
                tracking_number=order['row'].get('tracking_number', 0),
                order_id=order['row'].get('order_id', orden_servicio),
                customer_name=order['row'].get("customer_name", ""),
                city=order['row'].get("city", ""),
                product=order['row'].get("product", ""),
                category=order['row'].get("category", ""),
                status=order['row'].get("status", ""),
                carrier=order['row'].get("carrier", ""),
                track_url=order['row'].get("track_url", ""),
                notes=order['row'].get("notes", "") + f" Devolución registrada con código: {orden_devolucion}",
                delayed=order['row'].get("delayed", False),
                eta=order['row'].get("eta", ""),
                last_update=order['row'].get("last_update", ""),
                devolution_code=orden_devolucion
            )

            docs_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "docs")
            json_files = glob(os.path.join(docs_folder, "*.json"))
            try:
                for json_path in json_files:
                    try:
                        with open(json_path, "r", encoding="utf-8") as f:
                            content = f.read().strip()
                            if not content:
                                json_data = []
                            else:
                                json_data = json.loads(content)
                        json_data.append(order_response.dict())
                        with open(json_path, "w", encoding="utf-8") as f:
                            json.dump(json_data, f, ensure_ascii=False, indent=2)
                    except Exception:
                        return False
            except Exception:
                logger.error(f"Error al registrar la devolución en los archivos JSON.")
                return f"Error al registrar la devolución en los archivos JSON."
            return str(order_response)
        else:
            return f"Error al registrar la devolución en los archivos JSON."
    
    async def is_eligible_for_return(self, order_row: dict) -> tuple[bool, str]:
        """
        Determines if an order item is eligible for return based on its category and status.

        Args:
            order_row (dict): A dictionary representing an order item, expected to contain at least
                the keys "category" and "status".

        Returns:
            tuple[bool, str]: A tuple where the first element is a boolean indicating eligibility for return,
                and the second element is a message explaining the result.

        Rules:
            - Products in the categories "higiene", "cosméticos", "alimentos", or "bebidas" are not eligible for return.
            - Only products with status "Entregado" are eligible for return.
        """
        # Regla 5: Productos no elegibles por tipo
        tipo = order_row.get("category", "").lower()
        if any(palabra in tipo for palabra in ["higiene", "cosméticos", "alimentos", "bebidas"]):
            return False, "Productos de higiene personal, cosméticos, alimentos o bebidas no pueden ser devueltos."
        # Regla 6: Status debe ser 'Entregado'
        status = order_row.get("status", "")
        if status.strip().lower() != "entregado":
            return False, "Solo productos con status 'Entregado' pueden ser devueltos."
        return True, "Elegible para devolución."    
