import base64
import json
import os

from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from google.adk.agents import RunConfig, LiveRequestQueue
from google.adk.runners import InMemoryRunner
from google.genai import types

from app.core.config import settings
from app.agents import gmail_agent


async def start_agent_session(user_id, is_audio=False):

    runner = InMemoryRunner(app_name=settings.app_name, agent=gmail_agent)

    session = await runner.session_service.create_session(
        app_name=settings.app_name,
        user_id=user_id,
    )

    modality = "AUDIO" if is_audio else "TEXT"

    run_config = RunConfig(
        response_modalities=[modality],
        session_resumption=types.SessionResumptionConfig(),
    )

    live_request_queue = LiveRequestQueue()

    live_events = runner.run_live(
        session=session,
        live_request_queue=live_request_queue,
        run_config=run_config,
    )

    return live_events, live_request_queue


async def agent_to_client_sse(live_events):
    async for event in live_events:
        if event.turn_complete or event.interrupted:
            message = {
                "turn_complete": event.turn_complete,
                "interrupted": event.interrupted,
            }

            yield f"data: {json.dumps(message)}\n\n"
            print(f"[AGENT TO CLIENT] {message}")
            continue

        part: types.Part = (
            event.content and event.content.parts and event.content.parts[0]
        )

        if not part:
            continue

        is_audio = part.inline_data and part.inline_data.mime_type.startswith(
            "audio/pcm"
        )
        if is_audio:
            audio_data = part.inline_data and part.inline_data.data

            if audio_data:
                message = {
                    "mime_type": "audio/pcm",
                    "data": base64.b64encode(audio_data).decode("ascii"),
                }
                yield f"data: {json.dumps(message)}\n\n"
                print(f"[AGENT TO CLIENT]: audio/pcm {len(audio_data)} bytes")
                continue

        if part.text and event.partial:
            message = {
                "mime_type": "text/plain",
                "data": part.text,
            }
            yield f"data: {json.dumps(message)}\n\n"
            print(f"[AGENT TO CLIENT]: text/plain {message}")


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path("static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

active_sessions = {}


@app.get("/")
async def root():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/events/{user_id}")
async def sse_endpoint(user_id: int, is_audio: str = "false"):
    user_id_str = str(user_id)
    live_events, live_request_queue = await start_agent_session(
        user_id_str, is_audio == "true"
    )

    active_sessions[user_id_str] = live_request_queue

    print(f"Client #{user_id} connected via SSE, audio mode: {is_audio}")

    def cleanup():
        live_request_queue.close()
        if user_id_str in active_sessions:
            del active_sessions[user_id_str]
        print(f"Client #{user_id} disconnected from SSE")

    async def event_generator():
        try:
            async for data in agent_to_client_sse(live_events):
                yield data
        except Exception as e:
            print(f"Error in SSE stream: {e}")
        finally:
            cleanup()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
        },
    )

@app.post("/send/{user_id}")
async def send_message_endpoint(user_id: int, request: Request):
    user_id_str = str(user_id)

    live_request_queue = active_sessions[user_id_str]
    if not live_request_queue:
        return {"error": "Session not found"}

    message = await request.json()
    mime_type = message["mime_type"]
    data = message["data"]

    if mime_type == "text/plain":
        content = types.Content(role="user", parts=[types.Part.from_text(text=data)])
        live_request_queue.send_content(content=content)
        print(f"[CLIENT TO AGENT]: {data}")
    elif mime_type == "audio/pcm":
        decoded_data = base64.b64decode(data)
        live_request_queue.send_realtime(
            types.Blob(data=decoded_data, mime_type=mime_type)
        )
        print(f"[CLIENT TO AGENT]: audio/pcm {len(decoded_data)} bytes")
    else:
        return {"error": f"Mime type not supported: {mime_type}"}

    return {"status": "sent"}
