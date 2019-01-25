// var xhttp = new XMLHttpRequest();
// xhttp.onreadystatechange = function() {
//     if (this.readyState == 4 && this.status == 200) {
//       // i.e. if the state is 'response ready' and request is 'OK'
//       // do something with the response
//       document.getElementById("demo").innerHTML = this.responseText;
//     }
//   };
//   // Generate the request
//   xhttp.open("GET", "attendanceform.html?team=2", true);
//   xhttp.send();
// }

$(document).ready(function() {
    $("#id_team").change(function() {
        // show the speakers, want_to_judge, and submit button
        $("#div_id_speakers").show();
        $("#div_id_want_to_judge").show();
        $("#id_submit").show();
    });
});

$("#id_team").on('change', function() {
  console.log( $(this).val() );
  var team_id = $(this).val();

  $.ajax({
    url: 'ajax/filter_speakers_in_team/',
    data: {
      'team_id': team_id
    },
    dataType: 'json',
    success: function(data) {
      let speakers = data.speakers;
      $('#id_speakers option').hide();
      for (let i = 0; i < speakers.length; i++) {
        console.log(speakers[i]);
        $('#id_speakers option').filter(function() {
          return this.value == speakers[i];
        }).show();
      }
    }
  });
});
