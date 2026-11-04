from fastapi import FastAPI

app = FastAPI(title="Web Services API", version="1.0.0")

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