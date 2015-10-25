(function(){
  
  function Client(){
    var self = this;
    
    
    (function Constructor(rawdata){
      
    }).apply(this, arguments);
  }
  
  
  Client.get = function GetClient(onsuccess, onfailure){
    AuthGet('/api?method=users.validate', function(event){
      onsuccess(new Client(event));
    }, onfailure);
  }
  
  Client.login = function LoginClient(email, password, onsuccess, onfailure){
    AuthStringSet(email, password);
    Client.get(onsuccess, onfailure);
  }
  
  
  window.Client = Client;
  
})();