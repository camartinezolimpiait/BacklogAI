import requests
import json
import base64
import os
from app.config.settings import get_settings

# --- CONFIGURACIÓN DE ACCESO ---
# 1. Tu Organización de Azure DevOps
# Ejemplo: "tu_organizacion" (si tu URL es https://dev.azure.com/tu_organizacion)
ORG_NAME = get_settings().azure_devops_org_name

# 2. El Proyecto donde quieres crear la historia de usuario
PROJECT_NAME = get_settings().azure_devops_project_name

# 3. Token de Acceso Personal (PAT) de Azure DevOps
# Asegúrate de que tenga permisos de "Work Items (Read & Write)"
PAT = get_settings().azure_devops_token

# --- DEFINICIÓN DEL WORK ITEM ---
# La URL de la API REST para crear un Work Item (User Story en este caso)
# Usamos 'User Story' como tipo de Work Item. Si usas 'Feature', cámbialo aquí.
WORK_ITEM_TYPE = "Product Backlog Item"
API_URL = f"https://dev.azure.com/{ORG_NAME}/{PROJECT_NAME}/_apis/wit/workitems/${WORK_ITEM_TYPE}?api-version=7.1"



# --- FUNCIÓN PRINCIPAL ---

def createworkitem(str_description: str) -> None:
    """Crea una nueva Historia de Usuario en Azure DevOps usando la API REST."""

# El JSON que contiene la instrucción del Prompt Avanzado
# ESTE ES EL JSON QUE CREAMOS ANTERIORMENTE.
# NOTA: Los saltos de línea (\n) y las comillas escapadas (\\") son cruciales aquí.
    WORK_ITEM_BODY = [
        {
            "op": "add",
            "path": "/fields/System.Title",
            "value": "Generación Automática de Historias de Usuario: Tarea de Prompting AI"
        },
        {
            "op": "add",
            "path": "/fields/System.Description",
            "value": f"Se ha generado automáticamente una historia de usuario basada en la siguiente descripción:\n\n{str_description}"
        },
        {
            "op": "add",
            "path": "/fields/Custom.OITPMOPBIType",
            "value": "Improvement"
        }
    ]
    # 1. Configurar la Autenticación (Basic Auth con PAT)
    # Se codifica la cadena ":PAT" en Base64
    pat_encoded = base64.b64encode(f":{PAT}".encode('ascii')).decode('ascii')
    
    headers = {
        'Content-Type': 'application/json-patch+json',
        'Authorization': f'Basic {pat_encoded}'
    }

    print(f"Intentando crear Work Item ({WORK_ITEM_TYPE}) en {ORG_NAME}/{PROJECT_NAME}...")

    try:
        # 2. Enviar la Solicitud POST
        response = requests.post(
            API_URL, 
            headers=headers, 
            data=json.dumps(WORK_ITEM_BODY)
        )

        # 3. Procesar la Respuesta
        if response.status_code == 200:
            result = response.json()
            work_item_id = result.get('id')
            work_item_url = result.get('url')
            print("✅ Éxito: Historia de Usuario creada con éxito.")
            print(f"   ID del Work Item: **{work_item_id}**")
            print(f"   URL de la API: {work_item_url}")
            print(f"   URL en el navegador: {result.get('_links', {}).get('html', {}).get('href')}")
        else:
            print(f"❌ Error al crear el Work Item. Código de estado: {response.status_code}")
            print("   Mensaje de error:")
            # Intenta imprimir el mensaje de error del cuerpo de la respuesta
            try:
                error_details = response.json()
                print(json.dumps(error_details, indent=2))
            except json.JSONDecodeError:
                print(response.text)

    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")

# Ejecutar la función
if __name__ == "__main__":
    createworkitem("Sample Description for Work Item")
