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
  print(dbuser)

  if dbuser:
      if dbuser[3] == password:
          return JsonResponse({'success': True})
      else:
          return JsonResponse({'success': False, 'message': 'Invalid password'}, status=401)
  else:
      return JsonResponse({'success': False, 'message': 'User not found'}, status=404)
  # request.session['userid'] = request.body['userid']
  # request.session['password'] = request.body['password']

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


def thread_page(request):
  return render(request, "thread_page.html", {"username": "Alice"})

def block_page(request):
  return render(request, "block_page.html")

def my_block_page(request):
  return render(request, "my_block_page.html")

def message_page(request):
  return render(request, "message_page.html")

def profile_page(request):
  return render(request, "profile_page.html")