from fastapi import FastAPI
from api.catalogo_router import router as catalogo_router

app = FastAPI(title="Web Services API", version="1.0.0")
app.include_router(catalogo_router)

@app.get("/")
def read_root():
    return {"message": "¡Servidor activo y funcionando correctamente!"}

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "version": "1.0.0",
        "environment": "development"
    }