(function(){
  
  
  function OnResponse(request, onsuccess, onfail){
    var response = request.response;
    var json = JSON.parse(response);
    if (json.stat == 'fail'){
      onfail({
        code: json.error,
        message: json.message
      });
    }else{
      delete json['stat'];
      onsuccess(json);
    }
  }
  
  function OnError(event, callback){
    console.error('Unknown networking error');
  }
  
  window.APIPost = function APIPost(url, data, onsuccess, onfail, authheader){
    Post(url, data, function(event){
      OnResponse(event, onsuccess, onfail);
    }, function(event){
      OnError(event, onfail);
    }, authheader);
  }
  
  window.APIGet = function APIGet(url, onsuccess, onfail, authheader){
    Get(url, function(event){
      OnResponse(event, onsuccess, onfail);
    }, function(event){
      OnError(event, onfail);
    }, authheader);
  }
  
})();