from django.urls import re_path, path
from . import views


urlpatterns = [
    re_path(
        r"^confirm-email/(?P<key>[-:\w]+)/$",
        views.VerifyUserView.as_view(),
        name="verify_email",
    ),
    path("profile", views.UserProfileView.as_view(), name="profile"),
    path(
        "disable",
        views.DisableUserProfileView.as_view(),
        name="disable",
    ),
    path(
        "delete",
        views.DeleteUserProfileView.as_view(),
        name="delete",
    ),
]
