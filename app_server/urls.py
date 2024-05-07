from django.urls import include, path, re_path

from . import views

urlpatterns = [
  # enter page
  path("enter", views.enter_page, name="enter_page"),
  path("register", views.register, name="register"),
  path("login", views.login, name="login"),

  path("", views.thread_page, name="thread_page"),

  # block page
  path("block", views.block_page, name="block_page"),
  path("block/follow/<int:blockid>", views.follow_block, name="follow_block"),

  # message page
  path("message", views.message_page, name="message_page"),

  # profile page
  path("profile", views.profile_page, name="profile_page"),
  path("update-profile", views.update_profile, name="update_profile"),

  # my block page
  path("my-block", views.my_block_page, name="my_block_page"),
]
