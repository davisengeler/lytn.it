$(document).ready(function(){
	$("div#result").fadeIn("normal");
  	$("form").submit(function(e){
  	  link = $("input.textbox").val();
  	  $("input.textbox").replaceWith("<input id='textbox' type='text' class='textbox' name='link' placeholder='"+link+"'>");
  	  $("div#result").fadeOut("fast",function(){
  	    $("div#result").replaceWith("<div id='result'></div>");
  	  	$("div#result").load("https://api.lytn.it/shorten?dest="+escape(link),function(){
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
