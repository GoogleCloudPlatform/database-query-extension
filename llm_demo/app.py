# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from contextlib import asynccontextmanager
from typing import Optional

import uvicorn
from fastapi import APIRouter, Body, FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from google.auth.transport import requests  # type:ignore
from google.oauth2 import id_token  # type:ignore
from markdown import markdown
from piny import StrictMatcher, YamlLoader  # type: ignore
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

from orchestrator import BaseOrchestrator, createOrchestrator
routes = APIRouter()
templates = Jinja2Templates(directory="templates")


class AppConfig(BaseModel):
    host: IPv4Address | IPv6Address = IPv4Address("0.0.0.0")
    port: int = 8081
    clientId: Optional[str] = None
    orchestration: Optional[str]


def parse_config(path: str) -> AppConfig:
    with open(path, "r") as file:
        config = YamlLoader(path=path, matcher=StrictMatcher).load()
    return AppConfig(**config)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # FastAPI app startup event
    print("Loading application...")
    yield
    # FastAPI app shutdown event
<<<<<<< HEAD:llm_demo/app.py
    app.state.orchestration_type.close_clients()
=======
    close_client_tasks = [asyncio.create_task(a.close()) for a in ais.values()]

    asyncio.gather(*close_client_tasks)
>>>>>>> 30d0d92 (add orchestration interface):langchain_tools_demo/main.py


@routes.get("/")
@routes.post("/")
async def index(request: Request):
    """Render the default template."""
<<<<<<< HEAD:llm_demo/app.py
    # User session setup
    orchestrator = request.app.state.orchestration_type
    session = request.session
    if "uuid" not in session or not orchestrator.user_session_exist(session["uuid"]):
        await orchestrator.user_session_create(session)
=======
    # Agent setup
    agent = await get_agent(
        request.session,
        user_id_token=None,
        orchestration=request.app.state.orchestration,
    )
    templates = Jinja2Templates(directory="templates")
>>>>>>> 30d0d92 (add orchestration interface):langchain_tools_demo/main.py
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "messages": request.session["history"],
            "client_id": request.app.state.client_id,
        },
    )


@routes.post("/login/google", response_class=RedirectResponse)
async def login_google(
    request: Request,
):
    form_data = await request.form()
    user_id_token = form_data.get("credential")
    if user_id_token is None:
        raise HTTPException(status_code=401, detail="No user credentials found")

    client_id = request.app.state.client_id
    if not client_id:
        raise HTTPException(status_code=400, detail="Client id not found")
    user_name = get_user_name(str(user_id_token), client_id)

    # create new request session
<<<<<<< HEAD:llm_demo/app.py
    orchestrator = request.app.state.orchestration_type
    orchestrator.set_user_session_header(request.session["uuid"], str(user_id_token))
=======
    _ = await get_agent(request.session, str(user_id_token), orchestration=None)
>>>>>>> 30d0d92 (add orchestration interface):langchain_tools_demo/main.py
    print("Logged in to Google.")

    welcome_text = f"Welcome to Cymbal Air, {user_name}! How may I assist you?"
    if len(request.session["history"]) == 1:
        request.session["history"][0] = {
            "type": "ai",
            "data": {"content": welcome_text},
        }
    else:
        request.session["history"].append(
            {"type": "ai", "data": {"content": welcome_text}}
        )

    # Redirect to source URL
    source_url = request.headers["Referer"]
    return RedirectResponse(url=source_url)


@routes.post("/chat", response_class=PlainTextResponse)
async def chat_handler(request: Request, prompt: str = Body(embed=True)):
    """Handler for LangChain chat requests"""
    # Retrieve user prompt
    if not prompt:
        raise HTTPException(status_code=400, detail="Error: No user query")
    if "uuid" not in request.session:
        raise HTTPException(
            status_code=400, detail="Error: Invoke index handler before start chatting"
        )

    # Add user message to chat history
    request.session["history"].append({"type": "human", "data": {"content": prompt}})
<<<<<<< HEAD:llm_demo/app.py
    orchestrator = request.app.state.orchestration_type
    output = await orchestrator.user_session_invoke(request.session["uuid"], prompt)
    # Return assistant response
    request.session["history"].append({"type": "ai", "data": {"content": output}})
    return markdown(output)
=======
    ai = await get_agent(request.session, user_id_token=None, orchestration=None)
    try:
        print(prompt)
        # Send prompt to LLM
        response = await ai.invoke(prompt)
        # Return assistant response
        request.session["history"].append(
            {"type": "ai", "data": {"content": response["output"]}}
        )
        return markdown(response["output"])
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Error invoking agent: {err}")


async def get_agent(
    session: dict[str, Any], user_id_token: Optional[str], orchestration: Optional[str]
):
    global ais
    if "uuid" not in session:
        session["uuid"] = str(uuid.uuid4())
    id = session["uuid"]
    if "history" not in session:
        session["history"] = BASE_HISTORY
    if id not in ais:
        if not orchestration:
            raise HTTPException(status_code=500, detail="orchestration not provided.")
        ais[id] = await create(orchestration, session["history"])
    ai = ais[id]
    if user_id_token is not None:
        ai.client.headers["User-Id-Token"] = f"Bearer {user_id_token}"
    return ai
>>>>>>> 30d0d92 (add orchestration interface):langchain_tools_demo/main.py


@routes.post("/reset")
async def reset(request: Request):
    """Reset user session"""

    if "uuid" not in request.session:
        raise HTTPException(status_code=400, detail=f"No session to reset.")

    uuid = request.session["uuid"]
<<<<<<< HEAD:llm_demo/app.py
    orchestrator = request.app.state.orchestration_type
    if not orchestrator.user_session_exist(uuid):
        raise HTTPException(status_code=500, detail=f"Current user session not found")

    await orchestrator.user_session_reset(uuid)
=======
    global ais
    if uuid not in ais.keys():
        raise HTTPException(status_code=500, detail=f"Current agent not found")

    await ais[uuid].client.close()
    del ais[uuid]
>>>>>>> 30d0d92 (add orchestration interface):langchain_tools_demo/main.py
    request.session.clear()


def get_user_name(user_token_id: str, client_id: str) -> str:
    id_info = id_token.verify_oauth2_token(
        user_token_id, requests.Request(), audience=client_id
    )
    return id_info["name"]


def init_app(
    orchestration_type: Optional[str],
    client_id: Optional[str],
    secret_key: Optional[str],
) -> FastAPI:
    # FastAPI setup
    if orchestration_type is None:
        raise HTTPException(status_code=500, detail="Orchestrator not found")
    app = FastAPI(lifespan=lifespan)
    app.state.client_id = client_id
    app.state.orchestration_type = createOrchestrator(orchestration_type)
    app.include_router(routes)
    app.mount("/static", StaticFiles(directory="static"), name="static")
    app.add_middleware(SessionMiddleware, secret_key=secret_key)
    return app


if __name__ == "__main__":
    PORT = int(os.getenv("PORT", default=8081))
    HOST = os.getenv("HOST", default="0.0.0.0")
    ORCHESTRATION_TYPE = os.getenv("ORCHESTRATION_TYPE")
    CLIENT_ID = os.getenv("CLIENT_ID")
    SECRET_KEY = os.getenv("SECRET_KEY")
    app = init_app(ORCHESTRATION_TYPE, client_id=CLIENT_ID, secret_key=SECRET_KEY)
    if app is None:
        raise TypeError("app not instantiated")
    uvicorn.run(app, host=HOST, port=PORT)
