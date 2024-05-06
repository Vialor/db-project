from functools import wraps
import json
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from .models import (
  Users,
  Threads,
  Hoods,
  Blocks,
)

db = connection.cursor()

def i_logged_in(func):
  @wraps(func)
  def wrapper(request):
      userid = request.COOKIES.get('user_id')
      password = request.COOKIES.get('password')
      db.execute("""
        select * from Users
        where userid=%s
        """, [userid])
      dbuser = db.fetchone()
      if not dbuser or dbuser[3] != password:
          return JsonResponse({'message': 'Authentication Failed'}, status=401)
      func(request)
  return wrapper

def i_am_userid(target_userid):
    def decorator(func):
        @wraps(func)
        def wrapper(request):
            userid = request.COOKIES.get('user_id')
            if target_userid != userid:
               return JsonResponse({'message': 'Authentication Failed'}, status=401)
            password = request.COOKIES.get('password')
            db.execute("""
              select * from Users
              where userid=%s
              """, [userid])
            dbuser = db.fetchone()
            if not dbuser or dbuser[3] != password:
              return JsonResponse({'message': 'Authentication Failed'}, status=401)
            func(request)
        return wrapper
    return decorator

# Enter Page
def enter_page(request):
  return render(request, "enter_page.html")

@require_POST
def login(request):
  userid = request.POST.get('userid')
  password = request.POST.get('password')
  db.execute("""
    select * from Users
    where userid=%s
    """, [userid])
  dbuser = db.fetchone()
  if dbuser:
      if dbuser[3] == password:
          response = JsonResponse({'success': True})
          response.set_cookie('userid', userid)
          response.set_cookie('password', password)
          return response
      else:
          return JsonResponse({'success': False, 'message': 'Invalid password'}, status=401)
  else:
      return JsonResponse({'success': False, 'message': 'User not found'}, status=404)

@require_POST
def register(request):
  registerUsername = request.POST['username']
  registerPassword = request.POST['password']
  if not registerUsername or not registerPassword:
    return JsonResponse("Invalid username or password")
  
  db.execute("""
    insert into Users (userid, userName, password) 
    values((select max(userid) from users) + 1, """+registerUsername+""", """+registerPassword+""");
    """)
  
  return JsonResponse({"success": True})

@i_am_userid(0)
def thread_page(request):
  return render(request, "thread_page.html", {"username": "Alice"})

@i_am_userid(1)
def block_page(request):
  return render(request, "block_page.html")

@i_logged_in
def my_block_page(request):
  return render(request, "my_block_page.html")

def message_page(request):
  return render(request, "message_page.html")

def profile_page(request):
  return render(request, "profile_page.html")