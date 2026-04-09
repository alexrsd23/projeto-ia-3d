from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from brain_manager import manager

router = APIRouter(prefix="/api/brain", tags=["Brain Control"])

class ModeRequest(BaseModel):
    mode: str

@router.get("/mode")
def get_current_mode():
    return {"current_mode": manager.current_mode}

@router.post("/mode")
def set_mode(request: ModeRequest):
    try:
        manager.switch_mode(request.mode)
        return {"message": f"Modo alterado para {request.mode}", "current_mode": manager.current_mode}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/reset")
def reset_brain():
    manager.reset_memory()
    return {"message": f"Memória do cérebro ({manager.current_mode}) foi apagada com sucesso."}