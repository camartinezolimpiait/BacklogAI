#!/usr/bin/env python3
"""
EcoMarket RAG Solution - Main Entry Point
FastAPI application for RAG-based product queries and recommendations
"""

import sys
from pathlib import Path
from contextlib import asynccontextmanager
from app.api.apiFast import app
from app.front.grad import launch_gradio
#!/usr/bin/env python3
"""
EcoMarket RAG Solution - Main Entry Point
Lanzador de la API FastAPI
"""
if __name__ == "__main__":
    import threading
    import uvicorn
    from app.config.settings import get_settings
    from app.langchain.lang import LangAgent

    settings = get_settings()
    agent_executor = LangAgent().load_agent()

    def run_uvicorn():
        uvicorn.run(
            "app.api.apiFast:app",
            host=settings.host,
            port=settings.port,
            reload=settings.debug
        )

    # Lanzar FastAPI en un hilo
    uvicorn_thread = threading.Thread(target=run_uvicorn, daemon=True)
    uvicorn_thread.start()

    # Lanzar Gradio en el hilo principal
    launch_gradio(agent_executor, share=True, server_port=7000)