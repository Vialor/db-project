from django.urls import include, path, re_path

from . import views

urlpatterns = [
  path("", views.thread_page, name="thread_page"),
  path("block", views.block_page, name="block_page"),
  path("login", views.enter_page, name="enter_page"),
  path("message", views.message_page, name="message_page"),
  path("profile", views.thread_page, name="profile_page"),
  path("my-block", views.my_block_page, name="my_block_page"),
]
