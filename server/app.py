""" FLASK IMPORTS """
from flask import Flask, request, make_response, jsonify, abort
from functools import wraps


""" MONGO IMPORTS """
from utils.mongo_json_encoder import JSONEncoder


""" LOCAL IMPORTS """
from models import *
from constants import *
import response


""" FLASK SETUP """
app = Flask(__name__)


""" DECORATORS """
def auth(f):
  """
  ' PURPOSE
  '   Forces a given request to contain a valid Basic Authorization
  '   header using the UserModel as the auth database check.
  ' NOTES
  '   1. Adds an additional kwarg ( current_user ) which contains the
  '      entity of the current user based on the Basic Auth.
  """
  @wraps(f)
  def handle(*args, **kwargs):
    basic = request.authorization
    if not basic: return response.throw('100', compiled=True)
    
    email = basic.username
    password = basic.password
    
    users = AuthModel.fetch(AuthModel.email == email)
    print(email, users)
    if len(users) == 0: return response.throw('100', compiled=True)
    
    user = users[0]
    if not user.check_password(password): return response.throw('100', compiled=True)
    
    kwargs['current_user'] = user
    
    return f(*args, **kwargs)
  return handle

def parameters(*params):
  """
  ' PURPOSE
  '   Given a list of parameters, grabs them from the request's
  '   body (assumed to be json) and then adds them to the intended
  '   kwargs. Essentially removing the boilerplate to get body
  '   fields.
  ' PARAMETERS
  '   <str field_name1>
  '   <str field_name2>
  '   ...
  '   <str field_nameN>
  ' RETURNS
  '   Runs the original function and returns the result.
  ' NOTES
  '   1. Will throw error code 422 if an expected parameter is not
  '      present in the request body.
  """
  def decorator(f):
    @wraps(f)
    def scraper(*args, **kwargs):
      body = request.json
      for param in params:
        if not param in body: return response.throw('000', param, compiled=True)
        kwargs[param] = body[param]
      return f(*args, **kwargs)
    return scraper
  return decorator


#
#
#
# class Users(Resource):
#
#   @auth
#   def get(self, current_user):
#     return response.reply()
#
#
#
#
# class StudentUsers(Resource):
#
#   @parameters('email', 'password', 'name')
#   def post(self, email=None, password=None, name=None):
#     usertuple = StudentModel.create(email, password, name=name)
#     if not usertuple:
#       return response.throw('101')
#
#     user, auth = usertuple
#     return response.reply({
#       'id': user.key.urlsafe()
#     })
#
#
#
# class ParentUsers(Resource):
#
#   @parameters('email', 'password', 'name')
#   def post(self, email=None, password=None, name=None):
#     usertuple = ParentModel.create(email, password, name=name)
#     if not usertuple:
#       return response.throw('101')
#
#     user, auth = usertuple
#     return response.reply({
#       'id': user.key.urlsafe()
#     })



@app.route('/signup/faculty', methods=['POST'])
@parameters('email', 'password', 'name')
def signup_faculty(email=None, password=None, name=None):
  usertuple = FacultyModel.create(email, password, name=name)
  if not usertuple:
    return response.throw('101', compiled=True)
  
  user, auth = usertuple
  
  return response.reply({
    'id': user.key.urlsafe()
  }, compiled=True)



# must use super user to create other super user / view them

@app.route('/constants/errors', methods=['GET'])
def get_error_responses():
  return response.reply(response._ERROR_RESPONSES, compiled=True)




""" START SERVER """
if __name__ == '__main__':
    app.config['TRAP_BAD_REQUEST_ERRORS'] = True
    app.run(port=8080, debug=True)
