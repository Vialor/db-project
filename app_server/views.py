from functools import wraps
import json
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
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
      userid = request.COOKIES.get('userid')
      password = request.COOKIES.get('password')
      if not userid or not password:
         return JsonResponse({'message': 'Authentication Failed'}, status=401)
      db.execute("""
        select * from Users
        where userid=%s
        """, [userid])
      dbuser = db.fetchone()
      if not dbuser or dbuser[3] != password:
          return JsonResponse({'message': 'Authentication Failed'}, status=401)
      return func(request)
  return wrapper

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
  registerUsername = request.POST['r_username']
  registerPassword = request.POST['r_password']
  if not registerUsername or not registerPassword:
    return JsonResponse("Invalid username or password")
  
  db.execute("""
    insert into Users (userid, userName, password) 
    values((select max(userid) from users) + 1, """+registerUsername+""", """+registerPassword+""");
    """)
  
  return JsonResponse({"success": True})

def thread_page(request):
  return render(request, "thread_page.html", {"username": "Alice"})

def block_page(request):
  return render(request, "block_page.html")

def my_block_page(request):
  return render(request, "my_block_page.html")

def message_page(request):
  return render(request, "message_page.html")

# Profile Page
@i_logged_in
def profile_page(request):
  userid = request.COOKIES.get('userid')
  db.execute("""
    select * from Users
    where userid=%s
    """, [userid])
  dbuser = db.fetchone()
  columns = [col[0] for col in db.description]
  profile_info = {columns[i]: dbuser[i] for i in range(len(dbuser)) }
  return render(request, "profile_page.html", { "profile_info": profile_info })

@i_logged_in
@require_POST
def update_profile(request):
  userid = request.COOKIES.get('userid')
  username = request.POST.get('username')
  profile = request.POST.get('profile')
  db.execute("""
    update Users
      set username=%s, profile=%s
      where userID=%s
    """, [username, profile, userid])
  return redirect("profile_page")
  return JsonResponse({'message': 'Not authorized'}, status=401)