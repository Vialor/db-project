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
  path("block/apply/<int:blockid>", views.apply_join_block, name="apply_join_block"),

  # search page
  path("search", views.search_page, name="search_page"),

  # profile page
  path("profile", views.profile_page, name="profile_page"),
  path("update-profile", views.update_profile, name="update_profile"),

  # my block page
  path("my-block", views.my_block_page, name="my_block_page"),
  path("approve-application/<int:applicationid>", views.approve_application, name="approve_application"),
  
  # thread page
  path("thread", views.thread_page, name="thread_page"),
  path("thread_new", views.thread_page_new, name="thread_page_new"),
  path('thread/<int:thread_id>/', views.message_page, name='message_page'),
]
