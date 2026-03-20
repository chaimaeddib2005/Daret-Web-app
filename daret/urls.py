from django.urls import path
from . import views

urlpatterns = [
    path('login/',    views.login_view,    name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/',   views.logout_view,   name='logout'),
    path('',          views.dashboard,     name='dashboard'),
    path('circles/',                          views.circle_list,   name='circle_list'),
    path('circles/new/',                      views.circle_create, name='circle_create'),
    path('circles/<int:pk>/',                 views.circle_detail, name='circle_detail'),
    path('circles/<int:pk>/join/',            views.circle_join,   name='circle_join'),
    path('circles/<int:pk>/start/',           views.circle_start,  name='circle_start'),
    path('circles/<int:pk>/next-round/',      views.circle_next_round, name='circle_next_round'),
    path('circles/join-invite/',              views.join_by_invite, name='join_by_invite'),
    path('circles/<int:circle_pk>/approve/<int:user_id>/', views.approve_member,  name='approve_member'),
    path('circles/<int:circle_pk>/reject/<int:user_id>/',  views.reject_member,   name='reject_member'),
    path('circles/<int:circle_pk>/payout-order/<int:user_id>/', views.set_payout_order, name='set_payout_order'),
    path('circles/<int:circle_pk>/contributions/<int:contrib_pk>/paid/', views.mark_contribution_paid, name='mark_contribution_paid'),
    path('circles/<int:circle_pk>/contributions/<int:contrib_pk>/late/', views.mark_contribution_late, name='mark_contribution_late'),
    path('circles/<int:circle_pk>/disputes/new/',           views.raise_dispute,   name='raise_dispute'),
    path('circles/<int:circle_pk>/disputes/<int:dispute_pk>/resolve/', views.resolve_dispute, name='resolve_dispute'),
    path('finances/', views.my_finances, name='my_finances'),
    path('profile/',  views.profile,     name='profile'),
]
