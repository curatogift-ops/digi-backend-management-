from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from accounts.permissions import IsOwner
from accounts.serializers import (
    DigitechTokenSerializer,
    PasswordChangeSerializer,
    UserCreateSerializer,
    UserSerializer,
)
from activity.models import log_activity

User = get_user_model()


class LoginView(TokenObtainPairView):
    serializer_class = DigitechTokenSerializer


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class ChangePasswordView(generics.GenericAPIView):
    serializer_class = PasswordChangeSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        log_activity(request.user, 'password_changed', 'User', request.user.id, request=request)
        return Response({'detail': 'Password updated successfully.'})


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('first_name')
    filterset_fields = ['role', 'is_active_employee', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone']

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [permissions.IsAuthenticated()]
        return [IsOwner()]

    def perform_create(self, serializer):
        user = serializer.save()
        log_activity(self.request.user, 'employee_created', 'User', user.id, str(user), request=self.request)

    @action(detail=True, methods=['post'], permission_classes=[IsOwner])
    def deactivate(self, request, pk=None):
        user = self.get_object()
        user.is_active = False
        user.is_active_employee = False
        user.save()
        return Response(UserSerializer(user).data)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def health(request):
    return Response({'status': 'ok', 'app': 'Digitech Avenue CRM'})
