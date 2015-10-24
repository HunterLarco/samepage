""" GLOBAL IMPORTS """
import bcrypt


""" LOCAL IMPORTS """
import db
from constants import *




class BaseUserModel(db.Model):
  
  @classmethod
  def create(cls, email, password, **kwargs):
    if AuthModel.has_email(email):
      return None
    
    user = cls(**kwargs)
    user.save()
    
    auth = AuthModel(email=email, user=user)
    auth.set_password(password)
    auth.save()
    
    user.auth = auth
    user.save()
    
    return (user, auth)




class AuthModel(db.Model):
  
  """ PROPERTIES """
  email       = db.StringProperty     (required=True)
  password    = db.ByteStringProperty (required=True)
  user        = db.ModelProperty      (BaseUserModel, required=True)
  
  """ CONSTANTS """
  BCRYPT_ROUNDS = 12

  @classmethod
  def has_email(cls, email):
    query = cls.fetch(cls.email == email, count=1)
    return len(query) == 1

  def hash_password(self, password):
    password = password.encode('utf-8')
    hashed = bcrypt.hashpw(password, bcrypt.gensalt(self.BCRYPT_ROUNDS))
    return hashed
  
  def set_password(self, password):
    self.password = self.hash_password(password)
  
  def check_password(self, password):
    password = password.encode('utf-8')
    return bcrypt.hashpw(password, self.password) == self.password
  
  def to_dict(self):
    return {
      'email': self.email
    }








class StudentModel(BaseUserModel):
  
  auth    = db.ModelProperty(AuthModel)
  name    = db.StringProperty()

  def get_messages(self):
    return ConversationModel.fetch(ConversationModel.viewers == self.key)
  
  def get_faculty(self):
    return FacultyModel.fetch(FacultyModel.children == self.key)
  
  def get_parents(self):
    return ParentModel.fetch(ParentModel.children == self.key)






class FacultyModel(BaseUserModel):
  
  auth     = db.ModelProperty(AuthModel)
  name     = db.StringProperty()
  children = db.ModelProperty(StudentModel, multiple=True, default=[])
  
  def get_messages(self):
    return ConversationModel.fetch(ConversationModel.viewers == self.key)

  def add_child(self, email):
    auth = AuthModel.get(AuthModel.email == email)
    if not auth: return False
    self.children.append(auth.user)
    self.save()
    return True




class ParentModel(BaseUserModel):
  
  auth     = db.ModelProperty(AuthModel)
  name     = db.StringProperty()
  children = db.ModelProperty(StudentModel, multiple=True, default=[])
  
  def get_messages(self):
    return ConversationModel.fetch(ConversationModel.viewers == self.key)
  
  def add_child(self, email):
    auth = AuthModel.get(AuthModel.email == email)
    if not auth: return False
    self.children.append(auth.user)
    self.save()
    return True




class ConversationModel(db.Model):
  
  title    = db.StringProperty ()
  messages = db.KeyProperty    (multiple=True)
  viewers  = db.KeyProperty    (multiple=True, required=True)
  
  def get_messages(self):
    messages = []
    
    for key in self.messages:
      entity = key.get()
      if entity:
        messages.push(entity)
    
    return messages


class MessageModel(db.Model):
  
  author  = db.ModelProperty  (BaseUserModel, required=True)
  content = db.StringProperty (required=True)
  date    = db.FloatProperty  (required=True)
  
  @classmethod
  def create(cls, author, content):
    import time
    message = cls(author=author, content=content, date=time.time())
    message.save()
    return message


