from functools import wraps
import json
import traceback
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from .models import *

db = connection.cursor()

def i_logged_in(func):
  @wraps(func)
  def wrapper(request, *args, **kwargs):
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
      return func(request, *args, **kwargs)
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
def thread_page(request):
  try:
    userid = request.COOKIES.get('userid')
    thread_list = []
    
    # neighbor
    db.execute("""with A as (
    select tac.threadid
    from thread_authority tau
    join thread_accesses tac on tac.threadid = tau.threadid
    where tau.blockid = (
        select blockid
        from users
        where userid = %s))
    select threads.*
    from threads
    where threads.threadid in (
      select distinct A.threadid
      from A
      join messages m on m.threadid = A.threadid);""", userid)
    thread_neighbors = db.fetchall()
    columns = [col[0] for col in db.description]
    for thread_neighbor in thread_neighbors:
      thread_list.append({columns[i]: thread_neighbor[i] for i in range(len(thread_neighbor))})
      
    # friend
    db.execute("""with B as (
        (select useraid as friendid
        from friendship
        where userbid = %s)
        union
        (select userbid as friendid
        from friendship
        WHERE useraid = %s)
      )
      select threads.*
      from threads
      where threads.threadid in (
        select DISTINCT ta.threadid
        from messages m
        join thread_accesses ta on ta.threadid = m.threadid
        where m.authorid in (select friendid from B));""", [userid, userid])
    thread_friends = db.fetchall()
    columns = [col[0] for col in db.description]
    for thread_friend in thread_friends:
      thread_list.append({columns[i]: thread_friend[i] for i in range(len(thread_friend))})
      
    # followed blocks
    db.execute("""with C as (
        select tac.threadid
        from thread_authority tau
        join thread_accesses tac on tac.threadid = tau.threadid
        join block_followship bf on bf.blockid = tau.blockid
        where bf.userid = %s)
      select threads.*
      from threads
      where threads.threadid in (
        select distinct C.threadid
        from C
        join messages m on m.threadid = C.threadid);""", userid)
    thread_blocks = db.fetchall()
    columns = [col[0] for col in db.description]
    for thread_block in thread_blocks:
      thread_list.append({columns[i]: thread_block[i] for i in range(len(thread_block))})
      
    # followed hoods
    db.execute("""with D as (
      select tac.threadid
      from thread_authority tau
      join thread_accesses tac on tac.threadid = tau.threadid
      join blocks b on b.hoodid = tau.hoodid
      join block_followship bf on bf.blockid = b.blockid
      where bf.userid = %s and tau.blockid is null)
    select threads.*
    from threads
    where threads.threadid in (
      select distinct D.threadid
      from D
      join messages m on m.threadid = D.threadid);""", userid)
    thread_hoods = db.fetchall()
    columns = [col[0] for col in db.description]
    for thread_hood in thread_hoods:
      thread_list.append({columns[i]: thread_hood[i] for i in range(len(thread_hood))})
    
    return render(request, "thread_page.html", {"thread_list": thread_list})
  except:
    return JsonResponse({'message': 'Block Loading failed'}, status=401)
  
@i_logged_in
@require_POST
def message_page(request):
  return render(request, "message_page.html")

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
  except Exception as e:
    traceback.print_exc()  # Print the exception traceback:
    return JsonResponse({'message': 'Operation failed'}, status=401)

@require_POST
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

# My Block Page
@i_logged_in
def my_block_page(request):
  try:
    userid = request.COOKIES.get('userid')
    db.execute("""
      select * from Users
      where userid=%s
      """, [userid])
    dbuser = db.fetchone()
    db.execute("""
      select * from join_block_applications
      where blockid=%s
      """, [dbuser[1]])
    dbapplications = db.fetchall()
    columns = [col[0] for col in db.description]
    application_list = []
    for dbapplication in dbapplications:
      application_list.append({columns[i]: dbapplication[i] for i in range(len(dbapplication))})
    return render(request, "my_block_page.html", {"application_list": application_list})
  except Exception as e:
    traceback.print_exc()
    return JsonResponse({'message': 'Operation failed'}, status=401)

def search_page(request):
  return render(request, "search_page.html")

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