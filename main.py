from fastapi import FastAPI
from api.catalogo_router import router as catalogo_router
from api.parametro_router import router as parametro_router
from api.regla_comercial_router import router as regla_comercial_router
from api.usuario_router import router as usuario_router
from api.perfil_router import router as perfil_router
from api.notificacion_router import router as notificacion_router
from api.vuelo_router import router as vuelo_router
from api.oferta_vuelo_router import router as oferta_vuelo_router
from api.estado_vuelo_router import router as estado_vuelo_router
from api.hospedaje_router import router as hospedaje_router
from api.navegacion_router import router as navegacion_router
from api.transporte_router import router as transporte_router
from api.itinerario_router import router as itinerario_router
from api.clima_router import router as clima_router
from api.colaboracion_router import router as colaboracion_router


app = FastAPI(title="Web Services API", version="1.0.0")
app.include_router(catalogo_router)
app.include_router(parametro_router)
app.include_router(regla_comercial_router)
app.include_router(usuario_router)
app.include_router(perfil_router)
app.include_router(notificacion_router)
app.include_router(vuelo_router)
app.include_router(oferta_vuelo_router)
app.include_router(estado_vuelo_router)
app.include_router(hospedaje_router)
app.include_router(navegacion_router)
app.include_router(transporte_router)
app.include_router(colaboracion_router)
app.include_router(itinerario_router)
app.include_router(clima_router)


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
