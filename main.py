from fastapi import FastAPI
from api.catalogo_router import router as catalogo_router
from api.parametro_router import router as parametro_router
from api.regla_comercial_router import router as regla_comercial_router
from api.usuario_router import router as usuario_router
from api.perfil_router import router as perfil_router
from api.notificacion_router import router as notificacion_router
from api.vuelo_router import router as vuelo_router
from api.oferta_vuelo_router import router as oferta_vuelo_router

app = FastAPI(title="Web Services API", version="1.0.0")
app.include_router(catalogo_router)
app.include_router(parametro_router)
app.include_router(regla_comercial_router)
app.include_router(usuario_router)
app.include_router(perfil_router)
app.include_router(notificacion_router)
app.include_router(vuelo_router)
app.include_router(oferta_vuelo_router)

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