$(function() {
  var first_mail = $('div.mail:first')[0].id;

  function display(id) {
    var pos = {
      x: window.pageXOffset || document.body.scrollLeft,
      y: window.pageYOffset || document.body.scrollTop
    };
    $('ul.mailtree div.link').removeClass('selected');
    $('#link-' + id).addClass('selected').focus();
    $('div.mail').hide();
    $('h2:first').text($('h3', $('#' + id).show()).text());
    if (!(document.location.hash == '' && id == first_mail))
      document.location.href = '#' + id;
    window.scrollTo(pos.x, pos.y);
  }

  $('div.mail')
    .addClass('dynamic-mail')
    .appendTo($('<div></div>').insertBefore('div.mail:first'))
    .hide();
  $('div.mail h3').hide();

  $('div.link').each(function() {
    var id = $('a', $(this).parent()).attr('href').substr(1);
    $(this).click(function() {
      display(id);
      return false;
    });
  }).css({cursor: 'pointer'});

  var href = document.location.href.split(/#/, 2)[1];
  display(href != null ? href : first_mail);
});
