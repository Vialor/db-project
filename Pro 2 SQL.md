# SQL

```sql
@neighbor 
with A as (
    select tac.threadid
    from thread_authority tau
    join thread_accesses tac on tac.threadid = tau.threadid
    where tau.blockid = (
        select blockid
        from users
        where userid = %s))
    select *
    from threads
    join A on threads.threadid = A.threadid;

@new neighbor
with A as (
    select tac.threadid, lastAccess
    from thread_authority tau
    join thread_accesses tac on tac.threadid = tau.threadid
    where tau.blockid = (
        select blockid
        from users
        where userid = 12))
select *
from threads
join A on threads.threadid = A.threadid
left join messages m on m.threadid = A.threadid
where m.realtimestamp > A.lastAccess or A.lastAccess is null;





@new friend threads
with A as ((select useraid as friendid
    from friendship
    where userbid = 1) union
    (select userbid as friendid
    from friendship
    where useraid = 1))
select ta.threadid
from messages m
join thread_accesses ta on ta.threadid = m.threadid
where m.authorid in (select friendid from A) and (realtimestamp > lastaccess  or lastAccess is null);

@friend
with A as ((select useraid as friendid
    from friendship
    where userbid = 1) union
    (select userbid as friendid
    from friendship
    where useraid = 1))
select ta.threadid
from messages m
join thread_accesses ta on ta.threadid = m.threadid
where m.authorid in (select friendid from A);

@followed blocks new
with A as (
    select tac.threadid, lastAccess
    from thread_authority tau
    join thread_accesses tac on tac.threadid = tau.threadid
    join block_followship bf on bf.blockid = tau.blockid
    where bf.userid = 0)
select distinct A.threadid
from A
join messages m on m.threadid = A.threadid
where m.realtimestamp > A.lastAccess or A.lastAccess is null;

@followed blocks
with A as (
    select tac.threadid, lastAccess
    from thread_authority tau
    join thread_accesses tac on tac.threadid = tau.threadid
    join block_followship bf on bf.blockid = tau.blockid
    where bf.userid = 0)
select distinct A.threadid
from A
join messages m on m.threadid = A.threadid;

@followed hoods new
with A as (
    select tac.threadid, lastAccess
    from thread_authority tau
    join thread_accesses tac on tac.threadid = tau.threadid
    join blocks b on b.hoodid = tau.hoodid
    join block_followship bf on bf.blockid = b.blockid
    where bf.userid = 3 and tau.blockid is null)
select distinct A.threadid
from A
join messages m on m.threadid = A.threadid
where m.realtimestamp > A.lastAccess or A.lastAccess is null

@followed hoods
with A as (
    select tac.threadid
    from thread_authority tau
    join thread_accesses tac on tac.threadid = tau.threadid
    join blocks b on b.hoodid = tau.hoodid
    join block_followship bf on bf.blockid = b.blockid
    where bf.userid = 3 and tau.blockid is null)
select distinct A.threadid
from A
join messages m on m.threadid = A.threadid



@all threads for user 3
with A as (
    select tac.threadid
    from thread_authority tau
    join thread_accesses tac on tac.threadid = tau.threadid
    where tau.blockid = (
        select blockid
        from users
        where userid = 3)),
B as (
    select tac.threadid, lastAccess
    from thread_authority tau
    join thread_accesses tac on tac.threadid = tau.threadid
    join block_followship bf on bf.blockid = tau.blockid
    where bf.userid = 0),
C as ((select useraid as friendid
    from friendship
    where userbid = 3) union
    (select userbid as friendid
    from friendship
    where useraid = 3))
select distinct A.threadid
from A
join messages m on m.threadid = A.threadid
union
select distinct B.threadid
from B
join messages m on m.threadid = B.threadid
union
select ta.threadid
from messages m
join thread_accesses ta on ta.threadid = m.threadid
where m.authorid in (select friendid from C);
```

threadid backup

```sql
@Neighbor Threads(same block)
with A as (
    select tac.threadid
    from thread_authority tau
    join thread_accesses tac on tac.threadid = tau.threadid
    where tau.blockid = (
        select blockid
        from users
        where userid = 12))
select distinct A.threadid
from A
join messages m on m.threadid = A.threadid

@new neighbor threadid
with A as (
    select tac.threadid, lastAccess
    from thread_authority tau
    join thread_accesses tac on tac.threadid = tau.threadid
    where tau.blockid = (
        select blockid
        from users
        where userid = 12))
select distinct A.threadid
from A
join messages m on m.threadid = A.threadid
where m.realtimestamp > A.lastAccess or A.lastAccess is null;
```