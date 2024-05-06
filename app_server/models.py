# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
class Hoods(models.Model):
    hoodid = models.IntegerField(primary_key=True)
    hoodname = models.CharField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'hoods'

class Blocks(models.Model):
    blockid = models.IntegerField(primary_key=True)
    blockname = models.CharField(blank=True, null=True)
    hoodid = models.IntegerField(blank=True, null=True)
    coordinates = models.TextField(blank=True, null=True)  # This field type is a guess.

    class Meta:
        managed = False
        db_table = 'blocks'

class Users(models.Model):
    userid = models.IntegerField(primary_key=True)
    blockid = models.IntegerField(blank=True, null=True)
    username = models.CharField(blank=True, null=True)
    password = models.CharField(blank=True, null=True)
    profile = models.CharField(blank=True, null=True)
    photolink = models.CharField(blank=True, null=True)
    lastaccesstimestamp = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'users'

class Threads(models.Model):
    threadid = models.IntegerField(primary_key=True)
    subject = models.CharField(blank=True, null=True)
    publisherid = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'threads'
        
class BlockFollowship(models.Model):
    userid = models.IntegerField(primary_key=True)  # The composite primary key (userid, blockid) found, that is not supported. The first column is selected.
    blockid = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'block_followship'
        unique_together = (('userid', 'blockid'),)


class BlockMembershipRecord(models.Model):
    userid = models.IntegerField(primary_key=True)  # The composite primary key (userid, blockid) found, that is not supported. The first column is selected.
    blockid = models.IntegerField()
    lastleavetime = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'block_membership_record'
        unique_together = (('userid', 'blockid'),)


class Friendship(models.Model):
    useraid = models.IntegerField(primary_key=True)  # The composite primary key (useraid, userbid) found, that is not supported. The first column is selected.
    userbid = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'friendship'
        unique_together = (('useraid', 'userbid'),)


class FriendshipApplication(models.Model):
    senderid = models.IntegerField(primary_key=True)  # The composite primary key (senderid, recipientid) found, that is not supported. The first column is selected.
    recipientid = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'friendship_application'
        unique_together = (('senderid', 'recipientid'),)


class JoinBlockApplications(models.Model):
    applicationid = models.IntegerField(primary_key=True)
    userid = models.IntegerField(blank=True, null=True)
    blockid = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'join_block_applications'


class Messages(models.Model):
    messageid = models.IntegerField(primary_key=True)
    authorid = models.IntegerField(blank=True, null=True)
    threadid = models.IntegerField(blank=True, null=True)
    title = models.CharField(blank=True, null=True)
    textbody = models.CharField(blank=True, null=True)
    roottimestamp = models.DateTimeField(blank=True, null=True)
    coordinates = models.TextField(blank=True, null=True)  # This field type is a guess.
    replytoid = models.IntegerField(blank=True, null=True)
    realtimestamp = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'messages'


class Neighborhood(models.Model):
    followerid = models.IntegerField(primary_key=True)  # The composite primary key (followerid, followeeid) found, that is not supported. The first column is selected.
    followeeid = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'neighborhood'
        unique_together = (('followerid', 'followeeid'),)


class SpatialRefSys(models.Model):
    srid = models.IntegerField(primary_key=True)
    auth_name = models.CharField(max_length=256, blank=True, null=True)
    auth_srid = models.IntegerField(blank=True, null=True)
    srtext = models.CharField(max_length=2048, blank=True, null=True)
    proj4text = models.CharField(max_length=2048, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'spatial_ref_sys'


class ThreadAccesses(models.Model):
    threadid = models.IntegerField(primary_key=True)  # The composite primary key (threadid, memberid) found, that is not supported. The first column is selected.
    memberid = models.IntegerField()
    lastaccess = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'thread_accesses'
        unique_together = (('threadid', 'memberid'),)


class ThreadAuthority(models.Model):
    threadid = models.IntegerField(primary_key=True)
    hoodid = models.IntegerField(blank=True, null=True)
    blockid = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'thread_authority'

