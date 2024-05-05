from django.http import HttpResponse
from django.shortcuts import render

def thread_page(request):
  return render(request, "thread_page.html", {"username": "Alice"})

def enter_page(request):
  return render(request, "enter_page.html")

def block_page(request):
  return render(request, "block_page.html")

def my_block_page(request):
  return render(request, "my_block_page.html")

def message_page(request):
  return render(request, "message_page.html")

def profile_page(request):
  return render(request, "eprofile_page.html")