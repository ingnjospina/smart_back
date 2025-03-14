from django.urls import path

from .views import AlertasListView, LoginView, MedicionesCreateView, MedicionesFilesView, MedicionesListView, \
    MedicionesOne, MedicionesUpdateView, TranformadoresListView, UsuarioDetailView, UsuarioListCreateView, \
    InterruptoresListView, InterruptoresDetailView, TransformadoresDetailView


def name():
    print('hola'),


urlpatterns = [

    # USUARIOS
    path('login/', LoginView.as_view(), name='login'),
    path('usuarios/', UsuarioListCreateView.as_view(), name='usuario-list-create'),  # POST y GET (listar todos)
    path('usuarios/<int:id>/', UsuarioDetailView.as_view(), name='usuario-detail'),  # GET, PUT (usuario específico)

    # MEDICIONES
    path('mediciones/', MedicionesListView.as_view(), name='mediciones-list'),  # GET: Visualizar mediciones
    path('mediciones/total/<int:pk>/', MedicionesOne.as_view(), name='medicione-completa'),
    path('mediciones/create/', MedicionesCreateView.as_view(), name='mediciones-create'),  # POST: Insertar mediciones
    path('mediciones/<int:pk>/', MedicionesUpdateView.as_view(), name='mediciones-update'),  # PUT: Editar mediciones
    path('mediciones/file/<int:pk>', MedicionesFilesView.as_view(), name='file-Medicion'),
    # GET: obtener archivo medición

    # Alertas
    path('alertas/', AlertasListView.as_view(), name='alertas-list'),  # GET: Visualizar alertas

    # Transformadores
    path('tranformadores/', TranformadoresListView.as_view(), name='transformadores-list'),  # GET Transformadores
    path('tranformadores/<int:pk>/', TransformadoresDetailView.as_view(), name='transformadores-detail'),

    # Interruptores
    path('interruptores/', InterruptoresListView.as_view(), name='interruptores-list'),
    path('interruptores/<int:pk>/', InterruptoresDetailView.as_view(), name='interruptores-detail'),

]
