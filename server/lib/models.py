from google.appengine.ext import ndb
from google.appengine.ext.ndb import polymodel

import api



class InvalidAuthHeader(Exception):
  pass


class EmailUsedAlready(Exception):
  pass


class InvalidUserPermissions(Exception):
  pass


class InvalidPermissions(Exception):
  pass


class CannotCompleteGroupActionables(Exception):
  pass


class AuthUser(polymodel.PolyModel):
  email    = ndb.StringProperty(required=True, indexed=True)
  password = ndb.StringProperty(required=True)
  
  @classmethod
  def exists(cls, email):
    return cls.query(cls.email == email).count() != 0
  
  @classmethod
  def create(cls, email, password, save=True):
    if cls.exists(email):
      raise EmailUsedAlready()
    
    user = cls(email=email)
    user.set_password(password)
    if save: user.put()
    return user
  
  @classmethod
  def authenticate(cls, kwargname, permissions=None):
    def decorator(f):
      def checkauth(self, *args, **kwargs):
        user = cls.get_auth_user(self.request)

        if not user:
          raise InvalidAuthHeader()
        
        if permissions and not user.__class__ in permissions:
          raise InvalidUserPermissions()

        kwargs[kwargname] = user
        return f(self, *args, **kwargs)
      return checkauth
    return decorator
  
  @classmethod
  def get_auth_user(cls, request):
    import re
    
    if not 'authorization' in request.headers:
      return None
  
    authstring = request.headers['authorization']
    if re.match('^Basic\s[a-zA-Z0-9=]+$', authstring) == None:
      return None
  
    import base64
  
    try:
      rawauth = base64.b64decode(authstring[6:]).split(':')
    except:
      return None
      
    if len(rawauth) != 2:
      return None
  
    email, password = rawauth
  
    user = cls.query(cls.email == email).get()
    if user == None or not user.compare_password(password):
      return None
  
    return user
  
  def hash_password(self, password):
    from hashlib import sha256
    return sha256(password).hexdigest() 
  
  def set_password(self, password):
    self.password = self.hash_password(password)
  
  def compare_password(self, password):
    return self.password == self.hash_password(password)




class BasicUser(AuthUser):
  name = ndb.StringProperty()
  
  @classmethod
  def create(self, email, password, name=None, save=True):
    user = super(BasicUser, self).create(email, password, save=False)
    user.name = name
    if save: user.put()
    return user
  
  def to_dict(self):
    return {
      'name': self.name,
      'email': self.email
    }




class ActionableUser(BasicUser):
  actionables = ndb.KeyProperty(repeated=True)
  
  def add_actionable(self, actionable):
    self.actionables.append(actionable.key)
    self.put()
  
  def get_actionables(self):
    return [actionable.get() for actionable in self.actionables] if self.actionables else []
  
  def may_peek(self, user):
    return False
  
  def peek_actionables(self, user):
    if not self.may_peek(user):
      raise InvalidPermissions()
    return self.get_actionables()
  
  def complete_actionable(self, actionable):
    if not actionable.key in self.actionables:
      raise InvalidPermissions()
    actionable.complete()
  
  def send_message(self, actionable, content):
    if not actionable.key in self.actionables:
      raise InvalidPermissions()
    actionable.send_message(content, self)







class Actionable(polymodel.PolyModel):
  title = ndb.StringProperty(required=True)
  content = ndb.TextProperty(required=True)
  
  author = ndb.KeyProperty(required=True)
  created = ndb.DateTimeProperty(auto_now_add=True)
  
  messages = ndb.KeyProperty(repeated=True)
  
  completed = ndb.DateTimeProperty(indexed=True)
  duedate = ndb.DateTimeProperty(indexed=True)
  
  @classmethod
  def create(cls, title, content, members, author, duedate=None, in_group=False):
    actionable = cls(title=title, content=content, author=author.key, duedate=duedate)
    actionable.put()
    
    if not isinstance(members, list):
      members = [members]
    for member in members:
      member.add_actionable(actionable)
    
    if not in_group: author.add_actionable(actionable)
    
    return actionable
  
  def complete(self):
    from datetime import datetime
    self.completed = datetime.now()
    self.put()
  
  def has_duedate(self):
    return self.duedate != None
  
  def is_completed(self):
    return self.completed != None
  
  def get_messages(self):
    return self.messages if self.messages else []
  
  def get_age(self):
    import datetime
    return (datetime.datetime.now() - self.created).total_seconds()
  
  def get_completed_age(self):
    import datetime
    return (datetime.datetime.now() - self.completed).total_seconds()
  
  def get_due_time(self):
    import datetime
    return max(0, (self.duedate - datetime.datetime.now()).total_seconds())
  
  def to_dict(self):
    output = {}
    
    output['key'] = self.key.urlsafe()
    output['is_group'] = False
    output['title'] = self.title
    output['author'] = self.author.urlsafe()
    output['age'] = self.get_age()
    output['messages'] = [message.to_dict() for message in self.get_messages()]
    
    output['is_completed'] = self.is_completed()
    if self.is_completed(): output['completed'] = self.get_completed_age()

    output['has_duedate'] = self.has_duedate()
    if self.has_duedate(): output['duedate'] = self.get_due_time()
    
    return output
  
  def send_message(self, content, author):
    message = Message.create(content, author)
    self.messages.append(message.key)
    self.put()
  
  def get_messages(self):
    return [message.get() for message in self.messages]
    
    





class GroupActionable(polymodel.PolyModel):
  title = ndb.StringProperty()
  actionables = ndb.KeyProperty(repeated=True)
  
  @classmethod
  def create(cls, title, content, members, author, duedate=None):
    group = cls(title=title)
    
    if not isinstance(members, list):
      members = [members]
    for member in members:
      actionable = Actionable.create(title, content, member, author, duedate=duedate, in_group=True)
      group.actionables.append(actionable.key)
    group.put()
    
    author.add_actionable(group)
    
    return group
  
  def complete(self):
    raise CannotCompleteGroupActionables()
  
  def send_message(self, *args, **kwargs):
    for actionable in self.actionables:
      actionable.sendmessage(*args, **kwargs)
  
  def to_dict(self):
    return {
      'is_group': True,
      'title': self.title,
      'actionables': [actionable.get().to_dict() for actionable in self.actionables],
      'key': self.key.urlsafe()
    }





class Message(polymodel.PolyModel):
  content = ndb.TextProperty(required=True)
  author = ndb.KeyProperty(required=True)
  created = ndb.DateTimeProperty(auto_now_add=True)
  
  @classmethod
  def create(cls, content, author):
    message = cls(content=content, author=author.key)
    message.put()
    return message
  
  def get_age(self):
    import datetime
    return (datetime.datetime.now() - self.created).total_seconds()
  
  def to_dict(self):
    return {
      'content': self.content,
      'author': self.author.get().to_dict(),
      'age': self.get_age()
    }




class Student(ActionableUser):
  parents = ndb.KeyProperty(repeated=True)
  teachers = ndb.KeyProperty(repeated=True)
  
  def add_parent(self, parent):
    return self.add_parents([parent])
  
  def add_parents(self, parents):
    for parent in parents:
      if not isinstance(parent, Parent): continue
      if parent.key in self.parents: continue
      self.parents.append(parent.key)
    
    self.put()
    
    for parent in parents:
      if self.key in parent.students: continue
      parent.add_student(self)
  
  def add_teacher(self, teacher):
    return self.add_teachers([teacher])
  
  def add_teachers(self, teachers):
    for teacher in teachers:
      if not isinstance(teacher, Teacher): continue
      if teacher.key in self.teachers: continue
      self.teachers.append(teacher.key)
    
    self.put()
    
    for teacher in teachers:
      if self.key in teacher.students: continue
      teacher.add_student(self)




class Parent(ActionableUser):
  students = ndb.KeyProperty(repeated=True)
  
  def add_student(self, student):
    return self.add_students([student])
  
  def add_students(self, students):
    for student in students:
      if not isinstance(student, Student): continue
      if student.key in self.students: continue
      self.students.append(student.key)
    
    self.put()
    
    for student in students:
      if self.key in student.parents: continue
      student.add_parent(self)
  
  def may_peek(self, user):
    return user.key in self.students




class Teacher(ActionableUser):
  students = ndb.KeyProperty(repeated=True)
  
  def add_student(self, student):
    return self.add_students([student])
  
  def add_students(self, students):
    for student in students:
      if not isinstance(student, Student): continue
      if student.key in self.students: continue
      self.students.append(student.key)
    
    self.put()
    
    for student in students:
      if self.key in student.teachers: continue
      student.add_teacher(self)


