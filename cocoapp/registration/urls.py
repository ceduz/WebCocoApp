from django.urls import path
from .views import SignUpView, PersonalInformationUpdate
from .views import redirect_based_on_profile#, redirect_login

urlpatterns = [
    #path('', redirect_login, name='redirect_login'),
    #path('signup/', SignUpView.as_view(), name="signup"),
    path('redirect_based_on_profile/', redirect_based_on_profile, name='redirect_based_on_profile'),
    path('personal_information/', PersonalInformationUpdate.as_view(), name='personal_information'),
]