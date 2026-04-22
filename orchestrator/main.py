import importlib.util
import os
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="REVARIE LM V1 - Python Orchestrator")

# --- Surgical Import Logic for Hyphenated Folders ---
def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Load the Key Vault and Router
vault_path = os.path.join(os.path.dirname(__file__), "api-key-vault", "key_manager.py")
router_path = os.path.join(os.path.dirname(__file__), "model-router", "reasoning_router.py")

key_vault = load_module("key_manager", vault_path)
router = load_module("reasoning_router", router_path)

class Query(BaseModel):
    participant_id: str
    text: str

@app.get("/")
def home():
    return {"status": "CEO is active", "lobes": ["key-vault", "model-router", "task-scheduler"]}

@app.post("/orchestrate")
async def orchestrate(query: Query):
    # This coordinates the 18 keys and persona routing
    selected_key = key_vault.get_next_key() 
    target_model = router.route_query(query.text)
    
    return {
        "model": target_model,
        "key_index": selected_key,
        "action": "routing_to_provider"
    }
