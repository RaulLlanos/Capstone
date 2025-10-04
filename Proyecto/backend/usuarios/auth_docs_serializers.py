from rest_framework import serializers

class RegisterDocSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    rut_num = serializers.IntegerField(required=False)
    dv = serializers.CharField(required=False, max_length=1)
    rol = serializers.ChoiceField(choices=["tecnico", "administrador"])

class LoginDocSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    username = serializers.CharField(required=False)
    login = serializers.CharField(required=False)
    password = serializers.CharField()

class MeDocSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    rol = serializers.CharField()
