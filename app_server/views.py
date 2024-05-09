from functools import wraps
import json
import traceback
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_POST
import time
from datetime import datetime
from django.urls import reverse
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
    
    # my block feeds
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
      join messages m on m.threadid = A.threadid)
    order by threadid;""", [userid])
    thread_myblocks = db.fetchall()
    columns = [col[0] for col in db.description]
    thread_myblock_list = []
    for thread_myblock in thread_myblocks:
      thread_myblock_list.append({columns[i]: thread_myblock[i] for i in range(len(thread_myblock))})
      
    # my hood feeds
    db.execute("""with A as (
    select tac.threadid
    from thread_authority tau
    join thread_accesses tac on tac.threadid = tau.threadid
    where tau.hoodid = (
        select hoodid
        from blocks
        join users on blocks.blockid = users.blockid
        where userid = %s))
    select threads.*
    from threads
    where threads.threadid in (
      select distinct A.threadid
      from A
      join messages m on m.threadid = A.threadid)
    order by threadid;""", [userid])
    thread_myhoods = db.fetchall()
    columns = [col[0] for col in db.description]
    thread_myhood_list = []
    for thread_myhood in thread_myhoods:
      thread_myhood_list.append({columns[i]: thread_myhood[i] for i in range(len(thread_myhood))})
      
    # neighbor: followees
    db.execute("""SELECT t.*
    FROM Threads t
    JOIN (
        SELECT followeeid
        FROM Neighborhood
        WHERE followerid = %s
    )A ON t.publisherid = A.followeeid;""", [userid])
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
        where m.authorid in (select friendid from B) and (ta.memberid = %s))
      order by threadid;""", [userid, userid, userid])
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
        join messages m on m.threadid = C.threadid)
      order by threadid;""", [userid])
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
      join messages m on m.threadid = D.threadid)
    order by threadid;""", [userid])
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
      "thread_myblock": thread_myblock_list,
      "thread_myhood": thread_myhood_list,
    }})
  except Exception:
    traceback.print_exc()  # Print the exception traceback
    return JsonResponse({'message': 'Thread Page Broken.'}, status=401)
  
@i_logged_in
def thread_page_new(request):
  try:
    userid = request.COOKIES.get('userid')
    
    # my block feeds
    db.execute("""with A as (
    select tac.threadid, max(tac.lastAccess) as lastAccess
    from thread_authority tau
    join thread_accesses tac on tac.threadid = tau.threadid
    where tau.blockid = (
        select blockid
        from users
        where userid = %s)
        group by tac.threadid),
    b as (SELECT m.threadID, MAX(m.messageID) AS maxMessageID
    FROM Messages m
    GROUP BY m.threadID)
    select threads.*
    from threads
    where threads.threadid in (
      select distinct A.threadid
      from A
      join messages m on m.threadid = A.threadid
      join b on m.messageid = b.maxMessageID
      where m.realtimestamp > A.lastAccess or A.lastAccess is null)
    order by threadid;""", userid)
    thread_myblocks = db.fetchall()
    columns = [col[0] for col in db.description]
    thread_myblock_list = []
    for thread_myblock in thread_myblocks:
      thread_myblock_list.append({columns[i]: thread_myblock[i] for i in range(len(thread_myblock))})
      
    # my hood feeds
    db.execute("""with A as (
    select tac.threadid, max(tac.lastAccess) as lastAccess
    from thread_authority tau
    join thread_accesses tac on tac.threadid = tau.threadid
    where tau.hoodid = (
        select hoodid
        from blocks
        join users on blocks.blockid = users.blockid
        where userid = %s)
    group by tac.threadid),
    b as (SELECT m.threadID, MAX(m.messageID) AS maxMessageID
    FROM Messages m
    GROUP BY m.threadID)
    select threads.*
    from threads
    where threads.threadid in (
      select distinct A.threadid
      from A
      join messages m on m.threadid = A.threadid
      join b on m.messageid = b.maxMessageID
      where m.realtimestamp > A.lastAccess or A.lastAccess is null)
    order by threadid;""", userid)
    thread_myhoods = db.fetchall()
    columns = [col[0] for col in db.description]
    thread_myhood_list = []
    for thread_myhood in thread_myhoods:
      thread_myhood_list.append({columns[i]: thread_myhood[i] for i in range(len(thread_myhood))})
      
    # neighbor: followees
    db.execute("""with A as (
    select tac.threadid, max(tac.lastAccess) as lastAccess
    from thread_accesses tac
    join threads t on tac.threadid = t.threadid
    JOIN (
        SELECT followeeid
        FROM Neighborhood
        WHERE followerid = %s
    )A ON t.publisherid = A.followeeid
    group by tac.threadid),
    b as (SELECT m.threadID, MAX(m.messageID) AS maxMessageID
    FROM Messages m
    GROUP BY m.threadID)
    select threads.*
    from threads
    where threads.threadid in (
      select distinct A.threadid
      from A
      join messages m on m.threadid = A.threadid
      join b on m.messageid = b.maxMessageID
      where m.realtimestamp > A.lastAccess or A.lastAccess is null)
    order by threadid;""", userid)
    thread_neighbors = db.fetchall()
    columns = [col[0] for col in db.description]
    thread_neighbor_list = []
    for thread_neighbor in thread_neighbors:
      thread_neighbor_list.append({columns[i]: thread_neighbor[i] for i in range(len(thread_neighbor))})
      
    # friend
    db.execute("""with A as (
      (select useraid as friendid
      from friendship
      where userbid = %s) 
      union
      (select userbid as friendid
      from friendship
      where useraid = %s)),
      b as (SELECT m.threadID, MAX(m.messageID) AS maxMessageID
        FROM Messages m
        GROUP BY m.threadID)
      select threads.*
      from threads
      where threads.threadid in (
        select distinct ta.threadid
          from messages m
          join thread_accesses ta on ta.threadid = m.threadid
          JOIN B ON m.threadID = B.threadID
          JOIN (
              SELECT threadID, MAX(lastAccess) AS maxLastAccess
              FROM thread_accesses
              WHERE memberID = %s
              GROUP BY threadID
          ) AS maxAccess ON ta.threadID = maxAccess.threadID
          WHERE m.authorid IN (SELECT friendid FROM A)
            AND (m.realTimestamp > maxAccess.maxLastAccess OR maxAccess.maxLastAccess IS NULL)
            AND ta.memberid = %s
          )
      order by threadid;""", [userid, userid, userid, userid])
    thread_friends = db.fetchall()
    columns = [col[0] for col in db.description]
    thread_friends_list = []
    for thread_friend in thread_friends:
      thread_friends_list.append({columns[i]: thread_friend[i] for i in range(len(thread_friend))})
      
    # followed blocks
    db.execute("""with A as (
        select tac.threadid, max(tac.lastAccess) as lastAccess
        from thread_authority tau
        join thread_accesses tac on tac.threadid = tau.threadid
        join block_followship bf on bf.blockid = tau.blockid
        where bf.userid = %s
        group by tac.threadid),
        b as (SELECT m.threadID, MAX(m.messageID) AS maxMessageID
        FROM Messages m
        GROUP BY m.threadID)
      select threads.*
      from threads
      where threads.threadid in (
        select distinct A.threadid
        from A
        join messages m on m.threadid = A.threadid
        join b on m.messageid = b.maxMessageID
        where m.realtimestamp > A.lastAccess or A.lastAccess is null)
      order by threadid;""", [userid])
    thread_blocks = db.fetchall()
    columns = [col[0] for col in db.description]
    thread_blocks_list = []
    for thread_block in thread_blocks:
      thread_blocks_list.append({columns[i]: thread_block[i] for i in range(len(thread_block))})
      
    # followed hoods
    db.execute("""with A as (
      select tac.threadid, max(tac.lastAccess) as lastAccess
      from thread_authority tau
      join thread_accesses tac on tac.threadid = tau.threadid
      join blocks b on b.hoodid = tau.hoodid
      join block_followship bf on bf.blockid = b.blockid
      where bf.userid = %s and tau.blockid is null
      group by tac.threadid),
      b as (SELECT m.threadID, MAX(m.messageID) AS maxMessageID
      FROM Messages m
      GROUP BY m.threadID)
    select threads.*
    from threads
    where threads.threadid in (
      select distinct A.threadid
      from A
      join messages m on m.threadid = A.threadid
      join b on m.messageid = b.maxMessageID
      where m.realtimestamp > A.lastAccess or A.lastAccess is null)
    order by threadid;""", [userid])
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
      "thread_myblock": thread_myblock_list,
      "thread_myhood": thread_myhood_list,
    }})
  except Exception:
    traceback.print_exc()  # Print the exception traceback
    return JsonResponse({'message': 'New Thread Page Broken.'}, status=401)
  
@i_logged_in
def thread_page_neighbor(request):
  try:
    userid = request.COOKIES.get('userid')
    # neighbor: followees
    db.execute("""SELECT t.*
    FROM Threads t
    JOIN (
        SELECT followeeid
        FROM Neighborhood
        WHERE followerid = %s
    )A ON t.publisherid = A.followeeid;""", [userid])
    thread_neighbors = db.fetchall()
    columns = [col[0] for col in db.description]
    thread_neighbor_list = []
    for thread_neighbor in thread_neighbors:
      thread_neighbor_list.append({columns[i]: thread_neighbor[i] for i in range(len(thread_neighbor))})
    return render(request, "thread_page_neighbor.html", {"thread_list": {
      "thread_neighbor": thread_neighbor_list,
    }})
  except Exception:
    traceback.print_exc()  # Print the exception traceback
    return JsonResponse({'message': 'Thread Page Broken.'}, status=401)

@i_logged_in
def thread_page_friend(request):
  try:
    userid = request.COOKIES.get('userid')
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
        where m.authorid in (select friendid from B) and (ta.memberid = %s))
      order by threadid;""", [userid, userid, userid])
    thread_friends = db.fetchall()
    columns = [col[0] for col in db.description]
    thread_friends_list = []
    for thread_friend in thread_friends:
      thread_friends_list.append({columns[i]: thread_friend[i] for i in range(len(thread_friend))})
    return render(request, "thread_page_friend.html", {"thread_list": {
      "thread_friends": thread_friends_list,
    }})
  except Exception:
    traceback.print_exc()  # Print the exception traceback
    return JsonResponse({'message': 'Thread Page Broken.'}, status=401)
  
@i_logged_in
def thread_page_followed(request):
  try:
    userid = request.COOKIES.get('userid')
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
        join messages m on m.threadid = C.threadid)
      order by threadid;""", [userid])
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
      join messages m on m.threadid = D.threadid)
    order by threadid;""", [userid])
    thread_hoods = db.fetchall()
    columns = [col[0] for col in db.description]
    thread_hoods_list = []
    for thread_hood in thread_hoods:
      thread_hoods_list.append({columns[i]: thread_hood[i] for i in range(len(thread_hood))})
    return render(request, "thread_page_followed.html", {"thread_list": {
      "thread_blocks": thread_blocks_list,
      "thread_hoods": thread_hoods_list,
    }})
  except Exception:
    traceback.print_exc()  # Print the exception traceback
    return JsonResponse({'message': 'Thread Page Broken.'}, status=401)

@i_logged_in
def thread_page_my(request):
  try:
    userid = request.COOKIES.get('userid')
    # my block feeds
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
      join messages m on m.threadid = A.threadid)
    order by threadid;""", [userid])
    thread_myblocks = db.fetchall()
    columns = [col[0] for col in db.description]
    thread_myblock_list = []
    for thread_myblock in thread_myblocks:
      thread_myblock_list.append({columns[i]: thread_myblock[i] for i in range(len(thread_myblock))})
      
    # my hood feeds
    db.execute("""with A as (
    select tac.threadid
    from thread_authority tau
    join thread_accesses tac on tac.threadid = tau.threadid
    where tau.hoodid = (
        select hoodid
        from blocks
        join users on blocks.blockid = users.blockid
        where userid = %s))
    select threads.*
    from threads
    where threads.threadid in (
      select distinct A.threadid
      from A
      join messages m on m.threadid = A.threadid)
    order by threadid;""", [userid])
    thread_myhoods = db.fetchall()
    columns = [col[0] for col in db.description]
    thread_myhood_list = []
    for thread_myhood in thread_myhoods:
      thread_myhood_list.append({columns[i]: thread_myhood[i] for i in range(len(thread_myhood))})
      
    return render(request, "thread_page_my.html", {"thread_list": {
      "thread_myblock": thread_myblock_list,
      "thread_myhood": thread_myhood_list,
    }})
  except Exception:
    traceback.print_exc()  # Print the exception traceback
    return JsonResponse({'message': 'Thread Page Broken.'}, status=401)

@i_logged_in
def message_page(request, threadid):
  userid = request.COOKIES.get('userid')
  nowtime = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
  
  db.execute("""
    select lastaccess
    from thread_accesses
    where memberid = %s and threadid = %s;""", [userid, threadid])
  timestamp = db.fetchall()
  
  if not timestamp:
    db.execute("""
        update thread_accesses
          set lastaccess=%s
          where memberid = %s and threadid = %s and lastAccess IS NULL""", [nowtime, userid, threadid])
  else:
    db.execute("""
        update thread_accesses
          set lastaccess=%s
          where memberid = %s and threadid = %s
          """, [nowtime, userid, threadid])
  
  db.execute("""select *
  from messages
  join users u on messages.authorid = u.userid
  where messages.messageid in (
    select m.messageid
    from messages m 
    join thread_accesses tac on m.threadid = tac.threadid
    where m.threadid = %s and (m.realtimestamp < tac.lastAccess or tac.lastAccess is null))
  order by messageid""", [threadid])
  messages = db.fetchall()
  columns = [col[0] for col in db.description]
  messages_list = []
  for message in messages:
    messages_list.append({columns[i]: message[i] for i in range(len(message))})
  return render(request, "message_page.html", {'message_list': messages_list})

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

# Search Page
def search_page(request):
  return render(request, "search_page.html")

def keyword_search(request):
  keyword = request.POST.get('keyword')
  db.execute("""
    SELECT * FROM messages
    WHERE textbody LIKE %s
  """, ["%" + keyword + "%"])
  messages = db.fetchall()
  columns = [col[0] for col in db.description]
  message_list = []
  for message in messages:
    message_list.append({columns[i]: message[i] for i in range(len(columns))})
  return render(request, "search_page.html", {'message_list': message_list})

def geographic_search(request):
  location: tuple[int] = eval(request.POST.get('location'))
  radius = request.POST.get('radius')
  db.execute("""
    select *
    from messages
    where coordinates is not null and SQRT(POW(coordinates[0]-%s, 2) + POW(coordinates[1]-%s, 2)) < %s;
    """, [str(location[0]), str(location[1]), radius])
  messages = db.fetchall()
  columns = [col[0] for col in db.description]
  message_list = []
  for message in messages:
    message_list.append({columns[i]: message[i] for i in range(len(columns))})
  return render(request, "search_page.html", {'message_list': message_list})

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
  
@i_logged_in
@require_POST
def reply_message(request, threadid):
  try:
    userid = request.COOKIES.get('userid')
    replyid = request.POST.get('reply_to')
    replytitle = request.POST.get('reply_title')
    textbody = request.POST.get('reply_text')
    if not replyid or not textbody or not replytitle:
      return JsonResponse("Invalid reply action.")
    
    # TODO: if message id not in this thread
    
    db.execute("""select messages.roottimestamp 
      from messages
      where messages.messageid = %s""", [replyid])
    roottimestamp = db.fetchone()[0]
    if not roottimestamp:
      roottimestamp = datetime.fromtimestamp(0).strftime('%Y-%m-%d %H:%M:%S')
    nowtime = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
    
    db.execute("""insert into Messages (messageid, authorid, threadid, title, roottimestamp, textbody, replytoid, realtimestamp)
      select
        (select MAX(messageid) from Messages)+1,
        %s,
        %s,
        %s,
        %s,
        %s,
        %s,
        %s
      from Messages
      where messageid = %s;""", 
      [userid, threadid, replytitle, roottimestamp, textbody, replyid, nowtime, replyid])
    
    return redirect(reverse('message_page', args=[threadid]))
  except Exception:
    traceback.print_exc()
    return JsonResponse({'message': 'Operation failed'}, status=401)
  
@i_logged_in
@require_POST
def post_thread_block(request):
  try:
    userid = request.COOKIES.get('userid')
    threadSubject = request.POST.get('thread_subject')
    messageTitle = request.POST.get('message_title')
    messageText = request.POST.get('message_text')
    nowtime = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
    
    db.execute("""
      select max(threadid) from Threads;""")
    newthreadid = db.fetchone()[0] + 1
    
    db.execute("""insert into Threads (threadid, subject, publisherid)
    values(%s, %s, %s);""",[newthreadid, threadSubject, userid])
    
    db.execute("""insert into Messages (messageid, authorid, threadid, title, textbody, roottimestamp, realtimestamp)
    values((select max(messageid) from messages) + 1, %s, %s, %s, %s, %s, %s);""", [userid, newthreadid, messageTitle, messageText, nowtime, nowtime])
    
    db.execute("""
      select blockid from users where userid = %s;""", [userid])
    newblockid = db.fetchone()[0]
    db.execute("""
      select hoodid from blocks where blockid = %s;""", [newblockid])
    newhoodid = db.fetchone()[0]
    db.execute("""insert into thread_authority (threadid, hoodid, blockid)
    values(%s, %s, %s);""",[newthreadid, newhoodid, newblockid])
    
    # find all users in the same block
    db.execute("""
    select userid 
    from users
    where blockid = (select blockid
    from users
    where userid=%s)
    """, [userid])
    dballusers = db.fetchall()
    for dballuser in dballusers:
      userid_tmp = dballuser[0]
      db.execute("""
        INSERT INTO Thread_Accesses (threadID, memberID, lastaccess)
        VALUES (%s, %s, %s);""", 
        [newthreadid, userid_tmp, nowtime])
    
    return redirect("thread_page_my")
    
  except Exception:
    traceback.print_exc()
    return JsonResponse({'message': 'Operation failed'}, status=401)
  
  
@i_logged_in
@require_POST
def post_thread_hood(request):
  try:
    userid = request.COOKIES.get('userid')
    threadSubject = request.POST.get('thread_subject')
    messageTitle = request.POST.get('message_title')
    messageText = request.POST.get('message_text')
    nowtime = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
    
    db.execute("""
      select max(threadid) from Threads;""")
    newthreadid = db.fetchone()[0] + 1
    
    db.execute("""insert into Threads (threadid, subject, publisherid)
    values(%s, %s, %s);""",[newthreadid, threadSubject, userid])
    
    db.execute("""insert into Messages (messageid, authorid, threadid, title, textbody, roottimestamp, realtimestamp)
    values((select max(messageid) from messages) + 1, %s, %s, %s, %s, %s, %s);""", [userid, newthreadid, messageTitle, messageText, nowtime, nowtime])
    
    db.execute("""
      select blockid from users where userid = %s;""", [userid])
    newblockid = db.fetchone()[0]
    db.execute("""
      select hoodid from blocks where blockid = %s;""", [newblockid])
    newhoodid = db.fetchone()[0]
    db.execute("""insert into thread_authority (threadid, hoodid, blockid)
    values(%s, %s, %s);""",[newthreadid, newhoodid, None])
    
    # find all users in the same hood
    db.execute("""
    SELECT userID
    FROM Users u
    JOIN Blocks b ON u.blockID = b.blockID
    WHERE b.hoodID = (
      SELECT b.hoodID
      FROM Users u
      JOIN Blocks b ON u.blockID = b.blockID
      WHERE u.userID = %s
    );
    """, [userid])
    dballusers = db.fetchall()
    for dballuser in dballusers:
      userid_tmp = dballuser[0]
      db.execute("""
        INSERT INTO Thread_Accesses (threadID, memberID, lastaccess)
        VALUES (%s, %s, %s);""", 
        [newthreadid, userid_tmp, nowtime])
    
    return redirect("thread_page_my")
    
  except Exception:
    traceback.print_exc()
    return JsonResponse({'message': 'Operation failed'}, status=401)