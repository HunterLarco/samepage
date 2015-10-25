(function(){
  
  var authstring = '';
  
  window.addEventListener('load', function(){
    authstring = Cookies.get('authstring');
  });
  
  window.AuthStringSet = function AuthStringSet(email, password){
    authstring = BasicEncrypt(email, password);
    Cookies.set('authstring', authstring, {
      'expires': new Date(Date.now() + 30*24*60*60*1000)
    });
  }
  
  function BasicEncrypt(email, password){
    return btoa(email+':'+password);
  }
  
  window.AuthGet = function AuthGet(url, onsuccess, onfail){
    APIGet(url, onsuccess, onfail, 'Basic '+authstring);
  }
  
  window.AuthPost = function AuthGet(url, data, onsuccess, onfail){
    APIPost(url, data, onsuccess, onfail, 'Basic '+authstring);
  }
  
})();