""" ERROR RESPONSES """
_ERROR_RESPONSES = {
  '000' : 'Parameter missing: %s',
  
  '100' : 'User auth invalid',
  '101' : 'User email already used'
}


"""
' PURPOSE
'   Throws an error response, consisting of a error code
'   and error message.
' PARAMETERS
'   <int code>
'   <Tuple dataStruct>
'   <boolean **kwarg compiled>
' RETURNS
'   A dict containing...
'     <str stat> 'fail'
'     <int code> from parameters
'     <str message> corresponding error message from '__ERROR__RESPONSES__'
' NOTES
'   1. the 'dataStruct' is used to customize information in an error message
'   2. when compiled is true the dict is serialized into JSON format
"""
def throw(code, content=(), compiled=False):
  response = {
    'stat' : 'fail',
    'code' : code,
    'message' : _ERROR_RESPONSES[code] % content
  }
  return compile(response) if compiled else response


"""
' PURPOSE
'   Returns a successful response. May take additional data to add to the response.
' PARAMETERS
'   <Dict **kwarg data>
' RETURNS
'   A dict containing...
'     <str stat> 'ok'
'     <dict data>
"""
def reply(data={}, compiled=False):
  response = {
    'stat': 'ok',
    'data': data
  }
  return compile(response) if compiled else response


"""
' PURPOSE
'   JSON serializes a given dict
' PARAMETERS
'   <Dict JSON>
' RETURNS
'   A string
"""
def compile(JSON):
  import json
  return json.dumps(JSON)