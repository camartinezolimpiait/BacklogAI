custom_css = """
body {
    font-family: 'Segoe UI', Arial, sans-serif;
    background: linear-gradient(120deg, #e0f7fa 0%, #f4f6fa 100%);
    margin: 0;
    padding: 0;
}
.container {
    max-width: 80%;
    margin: 40px auto;
    background: #fff;
    border-radius: 16px;
    box-shadow: 0 4px 24px rgba(44, 62, 80, 0.12);
    padding: 32px 28px 24px 28px;
}
h2 {
    text-align: center;
    color: #388e3c;
    font-size: 2rem;
    margin-bottom: 18px;
    letter-spacing: 1px;
}
.chat-box {
    display: flex;
    flex-direction: column;
    gap: 18px;
}
.input-group {
    display: flex;
    gap: 10px;
}
#question {
    flex: 1;
    padding: 10px;
    border-radius: 8px;
    border: 1px solid #bdbdbd;
    font-size: 1.08rem;
    background: #f9fbe7;
}
#sendBtn, #clearBtn {
    padding: 10px 20px;
    border-radius: 8px;
    border: none;
    background: linear-gradient(90deg, #43a047 60%, #388e3c 100%);
    color: #fff;
    font-weight: bold;
    cursor: pointer;
    transition: background 0.2s;
}
#sendBtn:hover {
    background: linear-gradient(90deg, #388e3c 60%, #43a047 100%);
}
#clearBtn {
    background: #bdbdbd;
    color: #333;
}
#clearBtn:hover {
    background: #757575;
    color: #fff;
}
.history {
    max-height: 320px;
    overflow-y: auto;
    background: #f1f8e9;
    border-radius: 8px;
    border: 1px solid #c8e6c9;
    padding: 16px;
    margin-bottom: 8px;
}
.msg {
    margin-bottom: 14px;
    display: flex;
    flex-direction: column;
}
.msg.user {
    align-items: flex-end;
}
.msg.agent {
    align-items: flex-start;
}
.bubble {
    padding: 10px 16px;
    border-radius: 16px;
    max-width: 80%;
    font-size: 1rem;
    box-shadow: 0 2px 8px rgba(44,62,80,0.07);
}
.bubble.user {
    background: #c8e6c9;
    color: #2e7d32;
}
.bubble.agent {
    background: #fffde7;
    color: #333;
    border: 1px solid #ffe082;
}

.primary.svelte-o34uqh Specificity: (0,2,0)
 {
    border: var(--button-border-width) solid var(--button-primary-border-color);
    background: #047f22;
    color: var(--button-primary-text-color);
    box-shadow: var(--button-primary-shadow);
}
"""
import gradio as gr
from typing import List
from app.rag.retriever import DocumentRetriever
from app.rag.embeddings_hugging_face import EmbeddingHuggingFaceService
from app.config.settings import get_settings

# Instanciar el retriever globalmente para reusar la colección
settings = get_settings()
embedding_service = EmbeddingHuggingFaceService()
retriever = DocumentRetriever(embedding_service)

async def get_response(question: str, agent_executor) -> str:
    """
    Asynchronously processes a user's question by retrieving relevant context, constructing a prompt, and invoking an agent to generate a response.
    Args:
        question (str): The user's question to be answered.
        agent_executor: An agent capable of processing the constructed prompt and returning a response.
    Returns:
        str: The agent's answer to the question, or an error message if the input is invalid or processing fails.
    """

    if not question or not question.strip():
        return "Por favor ingresa una pregunta válida."
    else:
        query = question.strip()

    # Recuperar contexto relevante
    docs = await retriever.retrieve(query, 3)
    context = " --- ".join([doc['content'] for doc in docs]) if docs else ""

    # 2. Construir el prompt para el agente
    prompt = (
        "--- Contexto:\n{contexto}\n\n--- Pregunta:\n{pregunta}"
        .format(contexto=context, pregunta=question)
    )

    # 3. Ejecutar el agente
    agent_input = {"input": prompt, "context": context}
    response = agent_executor.invoke(agent_input)

    # 4. Extraer y retornar la respuesta
    output = response.get("output")
    if output:
        return output.strip()
    return str(response)

    # except Exception as e:
    #     return f"Error al procesar la consulta: {str(e)}"
 



def create_chat_interface(agent_executor):
    """
    Crea la interfaz de chat Gradio para EcoMarket RAG.
    - agent_executor: agente LangChain/LangGraph
    Returns: gr.Blocks demo
    """

    async def chat_function(message: str, history: List[dict[str, str]]) -> List[dict[str, str]]:
        """
        Procesa el mensaje del usuario y actualiza el historial de la conversación.
        """
        if not message or not message.strip():
            history.append({"role": "assistant", "content": "Por favor ingresa un mensaje válido."})
            return history
        try:
            # Añadir mensaje del usuario
            history.append({"role": "user", "content": message.strip()})

            # Construir historial para contexto
            history_str = "\n".join([f"{msg['role']}:{msg['content']}" for msg in history])
            response = await get_response(history_str, agent_executor)

            # Añadir respuesta del asistente
            history.append({"role": "assistant", "content": response})
            return history
        except Exception as e:
            error_msg = f"Error al procesar tu consulta: {str(e)}"
            history.append({"role": "assistant", "content": error_msg})
            return history

    with gr.Blocks(theme=gr.themes.Default(primary_hue=gr.themes.colors.green, secondary_hue=gr.themes.colors.lime),title="EcoMarket RAG Chat", css=custom_css) as demo:
        gr.Markdown(
            """
            # EcoMarket RAG Chat
            Bienvenido al asistente virtual de EcoMarket.
            Puedo ayudarte con:
            - Información de pedidos
            - Gestión de devoluciones
            - Políticas de la tienda
            """
        )

        chatbot = gr.Chatbot(
            label="EcoMarket Chatbot",
            height="80%",
            show_copy_button=True,
            bubble_full_width=False,
            type="messages",
        )

        msg = gr.Textbox(
            label="Tu mensaje",
            placeholder="Escribe tu pregunta aquí...",
            lines=2,
            show_label=False,
        )

        with gr.Row():
            submit_btn = gr.Button("Enviar", variant="primary")
            clear_btn = gr.Button("Limpiar", variant="secondary")

        # Enviar mensaje con Enter
        msg.submit(chat_function, inputs=[msg, chatbot], outputs=chatbot).then(
            lambda: gr.update(value=""), outputs=msg
        )
        # Enviar mensaje con botón
        submit_btn.click(chat_function, inputs=[msg, chatbot], outputs=chatbot).then(
            lambda: "", outputs=msg
        )
        # Limpiar historial
        clear_btn.click(lambda: [], None, chatbot, queue=False)

    return demo


def launch_gradio(agent_executor, share: bool = False, server_port: int = 7000):
    
    demo = create_chat_interface(agent_executor)

    demo.launch(
        share=share, server_port=server_port, server_name="127.0.0.1", show_error=True
    )

    return demo