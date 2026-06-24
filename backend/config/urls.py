from django.contrib import admin
from django.urls import path, include
# On importe les vues de Swagger (drf-spectacular)
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    #deuxb url :celui  ci dirige vers celui qui est dans api.urls(entre gererale-secrataire stage)
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    
    # --- ROUTES SWAGGER ---
    # Génère le fichier de schéma OpenAPI (le fichier JSON technique de l'API)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    
    # Affiche la superbe interface visuelle Swagger UI
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # Une alternative à Swagger (Redoc), optionnelle mais sympa
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
