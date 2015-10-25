from google.appengine.ext.webapp import blobstore_handlers


"""
' RESERVED ERROR CODES
'   -1 : Unspecified Method
'   -2 : Method Does Not Exist
'   -3 : Parameter(s) Missing
'   -4 : Incorrect JSON Formatting
'   -5 : <POST/GET> Method Not Supported
'    0 : Unknown Error
"""



def get(func):
  if hasattr(func, '__METHOD__'):
    setattr(func, '__METHOD__', getattr(func, '__METHOD__')+['GET'])
  else:
    setattr(func, '__METHOD__', ['GET'])
  return func

def post(func):
  if hasattr(func, '__METHOD__'):
    setattr(func, '__METHOD__', getattr(func, '__METHOD__')+['POST'])
  else:
    setattr(func, '__METHOD__', ['POST'])
  return func


def args(*args):
  def wrapper(func):
    if hasattr(func, '__ARGS__'):
      setattr(func, '__ARGS__', getattr(func, '__ARGS__')+list(args))
    else:
      setattr(func, '__ARGS__', list(args))
    return func
  return wrapper

def kwargs(*kwargs):
  def wrapper(func):
    if hasattr(func, '__KWARGS__'):
      setattr(func, '__KWARGS__', getattr(func, '__KWARGS__')+list(kwargs))
    else:
      setattr(func, '__KWARGS__', list(kwargs))
    return func
  return wrapper



"""
' Replaces file uploads with a BlobInfo instance for the corresponding blob
"""
class RequestHandler(blobstore_handlers.BlobstoreUploadHandler):
  # (Exception error, (int code, string message))
  ERROR_MAP = []
  
  @post
  def api_uploads_createurl(self, url):
    from google.appengine.ext import blobstore
    return {'url':blobstore.create_upload_url(url)}
  
  def __check_error_map__(self, error):
    for (error_type, (code, message)) in self.ERROR_MAP:
      if isinstance(error, error_type):
        return response.throw(code=code, message=message)
    
    import logging
    import traceback
    logging.error(traceback.format_exc())
    
    return response.throw()
  
  def __getfunc__(self):
    method = str(self.request.get('method')).replace('.','_')
    if method == '':
      return response.throw(code=-2, message='Unspecified Method')
    if not hasattr(self, method):
      return response.throw(code=-1, message='Method Does Not Exist')
    return response.reply({
      'function': getattr(self, method)
    })
  
  def __genargs__(self, func, getter):
    import inspect
    
    argspecs = inspect.getargspec(func)
    keyword_divide = -len(argspecs.defaults) if argspecs.defaults != None else len(argspecs.args)
    manualargs = getattr(func, '__ARGS__') if hasattr(func, '__ARGS__') else []
    defaultargs = argspecs.args[1:keyword_divide] + manualargs
    manualkwargs = getattr(func, '__KWARGS__') if hasattr(func, '__KWARGS__') else []
    keywordargs = argspecs.args[keyword_divide:] + manualkwargs
    
    args = []
    for arg in defaultargs:
      if getter(arg) != None:
        uploads = self.get_uploads(field_name=arg)
        if len(uploads) == 0:
         args.append(getter(arg))
        else:
          args.append(uploads[0])
    
    kwargs = {}
    for arg in keywordargs:
      if getter(arg) != None:
        uploads = self.get_uploads(field_name=arg)
        if len(uploads) == 0:
          kwargs[arg] = getter(arg)
        else:
          kwargs[arg] = uploads[0]
    
    return {
      'incomplete': len(args) != len(defaultargs),
      'args': args,
      'kwargs': kwargs
    }
  
  def __request__(self, getter):
    self.response.headers['Access-Control-Allow-Origin'] = '*'
    self.response.headers['Access-Control-Allow-Methods'] = 'PUT, GET, OPTIONS'
    self.response.headers['Access-Control-Allow-Credentials'] = 'true'
    self.response.headers['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept'
    self.response.headers['Content-Type'] = 'application/json'
    
    func = self.__getfunc__()
    if func['stat'] == 'fail':
      return self.write(func)
    func = func['function']
    
    if not hasattr(func, '__METHOD__') or not self.request.method in getattr(func, '__METHOD__'):
      return self.write(response.throw(code=-5, message='%s Method Not Supported' % self.request.method))
    
    args = self.__genargs__(func, getter)
    
    if args['incomplete']:
      return self.write(response.throw(code=-3, message='Parameter(s) Missing'))
    
    try:
      result = func(*args['args'], **args['kwargs'])
    except Exception as error:
      result = self.__check_error_map__(error)
    
    if result != None and 'stat' in result and result['stat'] == 'fail':
      self.write(result)
    else:
      self.write(response.reply({} if result == None else result))
  
  def write(self, obj):
    self.response.out.write(response.compile(obj))
  
  def get(self):
    self.__request__(lambda arg: self.request.get(arg) if self.request.get(arg) != '' else None)
  
  def post(self):
    if 'content-type' in self.request.headers and self.request.headers['content-type'].split(';')[0] == 'multipart/form-data':
      return self.get()
    
    from json import loads
    try:
      body = loads(self.request.body)
    except Exception:
      return self.write(response.throw(code=-4, message='Incorrect JSON Formatting'))
    self.__request__(lambda arg: body[arg] if arg in body else None)





class response:
  @classmethod
  def throw(cls, obj={}, code=0, message='Unknown Error', compiled=False):
    obj['stat'] = 'fail'
    obj['error'] = code
    obj['message'] = message
    return cls.compile(obj) if compiled else obj
  
  @classmethod
  def reply(cls, obj={}, compiled=False):
    obj['stat'] = 'ok'
    return cls.compile(obj) if compiled else obj
  
  @classmethod
  def compile(cls, obj):
    from json import dumps
    return dumps(obj, sort_keys=True, indent=2)