from functools import wraps
import json
import traceback
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
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
          response = redirect("profile_page")
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
      join messages m on m.threadid = A.threadid);""", [userid])
    thread_neighbors = db.fetchall()
    columns = [col[0] for col in db.description]
    thread_neighbor_list = []
    for thread_neighbor in thread_neighbors:
      thread_neighbor_list.append({columns[i]: thread_neighbor[i] for i in range(len(thread_neighbor))})
      
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
    thread_friends_list = []
    for thread_friend in thread_friends:
      thread_friends_list.append({columns[i]: thread_friend[i] for i in range(len(thread_friend))})
      
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
        join messages m on m.threadid = C.threadid);""", [userid])
    thread_blocks = db.fetchall()
    columns = [col[0] for col in db.description]
    thread_blocks_list = []
    for thread_block in thread_blocks:
      thread_blocks_list.append({columns[i]: thread_block[i] for i in range(len(thread_block))})
      
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
      join messages m on m.threadid = D.threadid);""", [userid])
    thread_hoods = db.fetchall()
    columns = [col[0] for col in db.description]
    thread_hoods_list = []
    for thread_hood in thread_hoods:
      thread_hoods_list.append({columns[i]: thread_hood[i] for i in range(len(thread_hood))})
    
    return render(request, "thread_page.html", {"thread_list": {
      "thread_neighbor": thread_neighbor_list,
      "thread_friends": thread_friends_list,
      "thread_blocks": thread_blocks_list,
      "thread_hoods": thread_hoods_list,
    }})
  except Exception:
    traceback.print_exc()  # Print the exception traceback
    return JsonResponse({'message': 'Thread Page Broken.'}, status=401)
  
@i_logged_in
def thread_page_new(request):
  try:
    userid = request.COOKIES.get('userid')
    
    # neighbor
    db.execute("""with A as (
    select tac.threadid, lastAccess
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
      join messages m on m.threadid = A.threadid
      where m.realtimestamp > A.lastAccess or A.lastAccess is null);""", userid)
    thread_neighbors = db.fetchall()
    columns = [col[0] for col in db.description]
    thread_neighbor_list = []
    for thread_neighbor in thread_neighbors:
      thread_neighbor_list.append({columns[i]: thread_neighbor[i] for i in range(len(thread_neighbor))})
      
    # friend
    db.execute("""with A as ((select useraid as friendid
      from friendship
      where userbid = 1) union
      (select userbid as friendid
      from friendship
      where useraid = 1))
      select threads.*
        from threads
        where threads.threadid in (
          select ta.threadid
          from messages m
          join thread_accesses ta on ta.threadid = m.threadid
          where m.authorid in (select friendid from A) and (realtimestamp > lastaccess  or lastAccess is null));""", [userid, userid])
    thread_friends = db.fetchall()
    columns = [col[0] for col in db.description]
    thread_friends_list = []
    for thread_friend in thread_friends:
      thread_friends_list.append({columns[i]: thread_friend[i] for i in range(len(thread_friend))})
      
    # followed blocks
    db.execute("""with A as (
        select tac.threadid, lastAccess
        from thread_authority tau
        join thread_accesses tac on tac.threadid = tau.threadid
        join block_followship bf on bf.blockid = tau.blockid
        where bf.userid = 0)
      select threads.*
      from threads
      where threads.threadid in (
        select distinct A.threadid
        from A
        join messages m on m.threadid = A.threadid
        where m.realtimestamp > A.lastAccess or A.lastAccess is null);""", userid)
    thread_blocks = db.fetchall()
    columns = [col[0] for col in db.description]
    thread_blocks_list = []
    for thread_block in thread_blocks:
      thread_blocks_list.append({columns[i]: thread_block[i] for i in range(len(thread_block))})
      
    # followed hoods
    db.execute("""with A as (
      select tac.threadid, lastAccess
      from thread_authority tau
      join thread_accesses tac on tac.threadid = tau.threadid
      join blocks b on b.hoodid = tau.hoodid
      join block_followship bf on bf.blockid = b.blockid
      where bf.userid = 3 and tau.blockid is null)
    select threads.*
    from threads
    where threads.threadid in (
      select distinct A.threadid
      from A
      join messages m on m.threadid = A.threadid
      where m.realtimestamp > A.lastAccess or A.lastAccess is null);""", userid)
    thread_hoods = db.fetchall()
    columns = [col[0] for col in db.description]
    thread_hoods_list = []
    for thread_hood in thread_hoods:
      thread_hoods_list.append({columns[i]: thread_hood[i] for i in range(len(thread_hood))})
    
    return render(request, "thread_page_new.html", {"thread_list": {
      "thread_neighbor": thread_neighbor_list,
      "thread_friends": thread_friends_list,
      "thread_blocks": thread_blocks_list,
      "thread_hoods": thread_hoods_list,
    }})
  except Exception:
    traceback.print_exc()  # Print the exception traceback
    return JsonResponse({'message': 'New Thread Page Broken.'}, status=401)
  
@i_logged_in
def message_page(request, threadid):
  db.execute("""select messages.*
  from messages
  where messages.messageid in (
    select m.messageid
    from messages m 
    join thread_accesses tac on m.threadid = tac.threadid
    where m.threadid = %s and (m.realtimestamp > tac.lastAccess or tac.lastAccess is null))
  order by messageid""", threadid)
  messages = db.fetchall()
  columns = [col[0] for col in db.description]
  messages_list = []
  for message in messages:
    messages_list.append({columns[i]: message[i] for i in range(len(message))})
  return render(request, "message_page.html", {'message': messages_list})

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
    traceback.print_exc()  # Print the exception traceback
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
  
@i_logged_in
def approve_application(request, applicationid):
  try:
    userid = request.COOKIES.get('userid')
    # TODO: check the application is in my block
    db.execute("""
      insert into join_block_approvers (applicationid, approverid) 
      values(%s, %s);
      """, [applicationid, userid])
    
    # if three have approved the application, change the applicant's block 
    db.execute("""
      select count(*) from join_block_approvers
      where applicationid=%s
      group by applicationid;
      """, [applicationid])
    approve_count = db.fetchone()[0]
    if approve_count >= 3:
      db.execute("""
        select * from join_block_applications
        where applicationid=%s
        """, [applicationid])
      (_, applicant_id, new_block_id) = db.fetchone()
      db.execute("""
      update Users
        set blockid=%s
        where userID=%s
        """, [new_block_id, applicant_id])
    return JsonResponse({'message': 'Operation succeeds'}, status=200)
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