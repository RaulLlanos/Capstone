from django.shortcuts import render

# Create your views here.

from rest_framework import viewsets
from .models import Usuario, Tecnico, Visita, Reagendamiento, HistorialVisita, EvidenciaServicio
from .serializers import UsuarioSerializer, TecnicoSerializer, VisitaSerializer, ReagendamientoSerializer, HistorialVisitaSerializer, EvidenciaServicioSerializer

class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer

class TecnicoViewSet(viewsets.ModelViewSet):
    queryset = Tecnico.objects.all()
    serializer_class = TecnicoSerializer

class VisitaViewSet(viewsets.ModelViewSet):
    queryset = Visita.objects.all()
    serializer_class = VisitaSerializer

class ReagendamientoViewSet(viewsets.ModelViewSet):
    queryset = Reagendamiento.objects.all()
    serializer_class = ReagendamientoSerializer

class HistorialVisitaViewSet(viewsets.ModelViewSet):
    queryset = HistorialVisita.objects.all()
    serializer_class = HistorialVisitaSerializer

class EvidenciaServicioViewSet(viewsets.ModelViewSet):
    queryset = EvidenciaServicio.objects.all()
    serializer_class = EvidenciaServicioSerializer