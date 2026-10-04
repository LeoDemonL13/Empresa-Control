from app.routes import (
    api_agente, api_auth, api_bitacora, api_categorias, api_dashboard,
    api_equipos, api_metricas, api_redes_sociales, api_reportes, api_users,
)

MODULOS_API = (
    api_auth, api_users, api_equipos, api_categorias, api_bitacora,
    api_agente, api_dashboard, api_metricas, api_redes_sociales, api_reportes,
)
