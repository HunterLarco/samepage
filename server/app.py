""" FLASK IMPORTS """
from flask import Flask, request, make_response, jsonify, abort
from flask_restful import Resource, Api


""" MONGO IMPORTS """
from utils.mongo_json_encoder import JSONEncoder


""" LOCAL IMPORTS """
from models import *
from constants import *
import response


""" FLASK SETUP """
app = Flask(__name__)
api = Api(app)


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
  def handle(*args, **kwargs):
    basic = request.authorization
    if not basic: return response.throw('100')
    
    email = basic.username
    password = basic.password
    
    users = AuthModel.fetch(AuthModel.email == email)
    print(email, users)
    if len(users) == 0: return response.throw('100')
    
    user = users[0]
    if not user.check_password(password): return response.throw('100')
    
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
    def scraper(*args, **kwargs):
      body = request.json
      for param in params:
        if not param in body: return response.throw('000', param)
        kwargs[param] = body[param]
      return f(*args, **kwargs)
    return scraper
  return decorator






class Users(Resource):
  
  @auth
  def get(self, current_user=None):
    return response.reply()
  
  @parameters('email', 'password', 'role')
  def post(self, email=None, password=None, role=None):
    if AuthModel.has_email(email):
      return response.throw('101')
    
    user = StudentModel(grade=5)
    user.save()
    
    auth = AuthModel(email=email, user=user)
    auth.set_password(password)
    auth.save()
    
    user.auth = auth
    user.save()
    
    return response.reply({
      'id': user.key.id
    })



# must use super user to create other super user / view them

class UserTypes(Resource):
  def get(self):
    return response.reply(USER_TYPES)


class ErrorTypes(Resource):
  def get(self):
    return response.reply(response._ERROR_RESPONSES)





""" RESTFUL API RESOURCE ROUTING """
api.add_resource(Users, '/users/')
api.add_resource(UserTypes, '/types/roles')
api.add_resource(ErrorTypes, '/types/errors')


""" CUSTOM JSON SERIALIZER FOR flask_restful """
@api.representation('application/json')
def output_json(data, code, headers=None):
    resp = make_response(JSONEncoder().encode(data), code)
    resp.headers.extend(headers or {})
    return resp


""" START SERVER """
if __name__ == '__main__':
    app.config['TRAP_BAD_REQUEST_ERRORS'] = True
    app.run(port=8080, debug=True)
