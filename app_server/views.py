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
          response = redirect("thread_page")
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
    values((select max(userid) from users) + 1, %s, %s);
    """, [registerUsername, registerPassword])
  
  return JsonResponse({"success": True})

@i_logged_in
@require_POST
def thread_page(request):
  try:
    userid = request.COOKIES.get('userid')
    db.execute("""with A as (
    select tac.threadid
    from thread_authority tau
    join thread_accesses tac on tac.threadid = tau.threadid
    where tau.blockid = (
        select blockid
        from users
        where userid = %s))
    select distinct A.threadid
    from A
    join messages m on m.threadid = A.threadid;""", userid)
    threads = db.fetchall()
    return render(request, "thread_page.html", {"threads": threads})
  except:
    return JsonResponse({'message': 'Operation failed'}, status=401)

# Block Page
@i_logged_in
def block_page(request):
  db.execute("""
    select * from Blocks
    """)
  dbblocks = db.fetchall()
  columns = [col[0] for col in db.description]
  block_list = []
  for dbblock in dbblocks:
     block_list.append({columns[i]: dbblock[i] for i in range(len(dbblock)) })
  return render(request, "block_page.html", { "block_list": block_list })

@require_POST
@i_logged_in
def follow_block(request, blockid):
  try:
    userid = request.COOKIES.get('userid')
    db.execute("""
      insert into block_followship (userid, blockid)
      values(%s, %s);
      """, [userid, blockid])
    return JsonResponse({'message': 'Operation succeeds'}, status=200)
  except:
    return JsonResponse({'message': 'Operation failed'}, status=401)

@i_logged_in
def apply_join_block(request, blockid):
  try:
    userid = request.COOKIES.get('userid')
    db.execute("""
      insert into Join_Block_Applications (applicationid, userID, blockID)
	    values((select max(applicationid) from Join_Block_Applications) + 1, %s, %s);
      """, [userid, blockid])
    return JsonResponse({'message': 'Operation succeeds'}, status=200)
  except:
    return JsonResponse({'message': 'Operation failed'}, status=401)

@i_logged_in
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
  try:
    userid = request.COOKIES.get('userid')
    username = request.POST.get('username')
    profile = request.POST.get('profile')
    db.execute("""
      update Users
        set username=%s, profile=%s
        where userID=%s
      """, [username, profile, userid])
    return redirect("profile_page")
  except:
    return JsonResponse({'message': 'Operation failed'}, status=401)