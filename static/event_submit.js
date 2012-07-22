jQuery.noConflict()(function($) {
  
(function() {
  var e = document.createElement('script'); e.async = true;
  e.src = document.location.protocol + '//connect.facebook.net/en_US/all.js';
  document.getElementById('fb-root').appendChild(e);
}());
  
$('form').submit(function () {
  var names = [];
  var friendSelector = $("#jfmfs-container").data('jfmfs');
  var friends = friendSelector.getSelectedIdsAndNames();
  for (var i in friends) {
    var name = friends[i].name;
    if (name) {
      names.push(friends[i].name);
    }
  }
  names.push(constants.name);
  names.sort(function(a, b) {
    return a.split(':')[2] < b.split(':')[2] ? -1 : 1;
  });

  names = '\n\nBuilt by '+names.join(', ');

  if (!$('#name').val()) {
    alert('A hack isn\'t very much without a catchy name.');
    return false;
  }
  if (!$('#description').val()) {
    alert('Write a description, yo.');
    return false;
  }
  if (!$('#hack_url').val() || $('#hack_url').val() == 'http://') {
    alert('Where does your hack live? Put in a hack url please.');
    return false;
  }
  if (!$('#screenshot_url').val() || $('#screenshot_url').val() == 'http://') {
    alert('A screenshot is worth a thousand words.');
    return false;
  }
  function is_valid_url(url) {
    return url.match(/^(ht|f)tps?:\/\/[a-z0-9-\.]+\.[a-z]{2,4}\/?([^\s<>\#%"\,\{\}\\|\\\^\[\]`]+)?$/) !== null;
  }
  if (!is_valid_url($('#hack_url').val())) {
    alert('Your hack URL doesn\'t look like a valid URL.');
    return false;
  }
  if (!is_valid_url($('#screenshot_url').val())) {
    alert('Your screenshot URL doesn\'t look like a valid URL.');
    return false;
  }

  var img = document.createElement('img');
  var description = $('#description').val();
  if (description.charAt(description.length) !== ".") {
    description += '.';
  }
  description += names;

  img.onload = function() {
    /*
    var data = {
      method: 'stream.publish',
      attachment: {
        name: $('#name').val(),
        description: description,
        href: $('#hack_url').val(),
        media: [
          { type: 'image', src: $('#screenshot_url').val(), href: $('#screenshot_url').val() }
        ],
      },
      target_id: $('#eid').val(),
      user_message: {value: 'Submit your hack.'},
    };
    if ($('#source_url').val() && $('#source_url').val() != 'http://github.com/.../...') {
      data['action_links'] = [
        { text: 'View Code', href: $('#source_url').val() },
      ];
    }
    
    FB.ui(data, function(response) {
      if (response && response.post_id) {
        alert('Submission was published. Go get everyone to like it to win the Community Choice prize.');
        window.location = constants.eid;
      } else {
        alert('Failed. Was everything filled out (and were all the URLs valid)?');
      }
    });
    */

    var data = {
      'message': $('#name').val(),
      'link': $('#hack_url').val(),
      'picture': $('#screenshot_url').val(),
      'name': $('#name').val(),
      'description': description
    };
    if ($('#source_url').val() && $('#source_url').val() != 'http://github.com/.../...') {
      data['actions'] = [
        { name: 'View Code', link: $('#source_url').val() },
      ];
    }
    
    FB.api($('#eid').val() + '/feed', 'post', data, function(response) {
      if (typeof response.error !== "undefined") {
        alert(response.error.message);
      }
      if (!response.id) {
        alert('Bad response: '+response);
      }
      window.location = 'http://facebook.com/'+response.id;
    });

    /*
    var data = {
      method: 'stream.publish',
      message: $('#name').val() + '\n' + description + '\nImage: ' + $('#screenshot_url').val() + '\nLink: ' + $('#hack_url').val(),
      attachment: {
        caption: $('#name').val(),
        name: $('#name').val(),
        description: description,
        href: $('#hack_url').val(),
        media: [
          { type: 'image', src: $('#screenshot_url').val(), href: $('#screenshot_url').val() }
        ],
      },
      target_id: $('#eid').val(),
    };
    if ($('#source_url').val() && $('#source_url').val() != 'http://github.com/.../...') {
      data['action_links'] = [
        { text: 'View Code', href: $('#source_url').val() },
      ];
    }

    console.log(data);
    FB.api(data, function(response) {
      console.log(response);
      if (response) {
        alert('Submission was published. Go get everyone to like it to win the Community Choice prize.');
        window.location = constants.eid;
      } else {
        alert('Failed. Was everything filled out (and were all the URLs valid)?');
      }
    });
    */
  }
  
  img.onerror = function() {
    var msg = 'Try putting it in your web browser and make sure it loads just an image.';
    if ($('#screenshot_url').val().search('localhost') !== -1) {
      msg = 'You can\'t use localhost. Please upload to tinypic.com or something similar.';
    }
    alert('Your image URL isn\'t valid. '+msg);
  }
  img.src = $('#screenshot_url').val();
  $(document).append(img);
  return false;
});

});
