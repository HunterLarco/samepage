""" GLOBAL IMPORTS """
import bcrypt


""" LOCAL IMPORTS """
import db
from constants import *




class BaseUserModel(db.Model):
  pass




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
  
  auth  = db.ModelProperty(AuthModel)
  grade = db.IntegerProperty()
