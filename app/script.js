$(document).ready(function(){
	$("div#result").fadeIn("normal");
  	$("form").submit(function(e){
  	  link = $("input.textbox").val();
  	  $("input.textbox").replaceWith("<input id='textbox' type='text' class='textbox' name='link' placeholder='"+link+"'>");
  	  $("div#result").fadeOut("fast",function(){
  	    $("div#result").replaceWith("<div id='result'></div>");
  	  	$("div#result").load("https://jbhxd6g6a0.execute-api.us-east-1.amazonaws.com/shorten?dest="+escape(link),function(){
          dataLayer.push({
            'event':'response'
          });
  	  		$("div#result").fadeIn("normal");
  	  	});
  	  });
  	});
});
function validateForm(){
   	return false;
}