import webapp2
from google.appengine.ext.webapp import template
import os


from lib import api
from lib.models import *


class APIHandler(api.RequestHandler):
  ERROR_MAP = [
    (InvalidAuthHeader              , (100, 'Invalid authentification header')),
    (EmailUsedAlready               , (101, 'Email address already in use')),
    (InvalidUserPermissions         , (102, 'Endpoint is not available for given user')),
    (InvalidPermissions             , (103, 'Invalid permissions')),
    (CannotCompleteGroupActionables , (104, 'Cannot complete a group actionable. Only individual actionables'))
  ]
  
  @api.get
  @AuthUser.authenticate('user')
  def users_validate(self, user=None):
    pass
  
  @api.post
  def users_signup_student(self, email, password, name):
    user = Student.create(email, password, name)
    return {
      'key': user.key.urlsafe()
    }
  
  @api.post
  def users_signup_parent(self, email, password, name):
    user = Parent.create(email, password, name)
    return {
      'key': user.key.urlsafe()
    }
  
  @api.post
  def users_signup_teacher(self, email, password, name):
    user = Teacher.create(email, password, name)
    return {
      'key': user.key.urlsafe()
    }
  
  @api.get
  @api.kwargs('user')
  @AuthUser.authenticate('current_user')
  def actionables(self, user=None, current_user=None):
    if user: user = ndb.Key(urlsafe=user).get()

    if user == None:
      actionables = current_user.get_actionables()
    else:
      actionables = current_user.peek_actionables(user)
    
    return {
      'actionables': [actionable.to_dict() for actionable in actionables]
    }
  
  @api.post
  @api.args('title', 'content', 'members')
  @api.kwargs('duedate', 'is_group')
  @AuthUser.authenticate('user')
  def actionables_create(self, title, content, members, user=None, duedate=None, is_group=False):
    if not isinstance(members, list):
      members = [members]
    members = [ndb.Key(urlsafe=member).get() for member in members]
    
    if is_group:
      actionable = GroupActionable.create(title, content, members, user, duedate=duedate)
    else:
      actionable = Actionable.create(title, content, members, user, duedate=duedate)
      
    return actionable.to_dict()
  
  @api.post
  @api.args('actionable')
  @AuthUser.authenticate('user')
  def actionables_complete(self, actionable, user=None):
    actionable = ndb.Key(urlsafe=actionable).get()
    user.complete_actionable(actionable)
  
  @api.post
  @api.args('students')
  @AuthUser.authenticate('user', permissions=[Parent, Teacher])
  def students_add(self, students, user=None):
    if not isinstance(students, list):
      students = [students]
    students = [ndb.Key(urlsafe=student).get() for student in students]
    user.add_students(students)
  
  @api.post
  @api.args('parents')
  @AuthUser.authenticate('user', permissions=[Student])
  def parents_add(self, parents, user=None):
    if not isinstance(parents, list):
      parents = [parents]
    parents = [ndb.Key(urlsafe=parent).get() for parent in parents]
    user.add_parents(parents)
  
  @api.post
  @api.args('content', 'actionable')
  @AuthUser.authenticate('user')
  def messages_send(self, content, actionable, user=None):
    actionable = ndb.Key(urlsafe=actionable).get()
    user.send_message(actionable, content)
    
    






class MainHandler(webapp2.RequestHandler):
  def get(self):
    template_values = {}
    path = os.path.join(os.path.dirname(__file__), 'pages/main.html')
    self.response.out.write(template.render(path, template_values))
    
  


app = webapp2.WSGIApplication([
  ('/api(?:/.*)?', APIHandler),
  ('.*', MainHandler)
], debug=True)