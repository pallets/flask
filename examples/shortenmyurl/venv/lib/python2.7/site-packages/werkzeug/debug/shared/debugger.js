$(function() {
  var sourceView = null;

  /**
   * if we are in console mode, show the console.
   */
  if (CONSOLE_MODE && EVALEX) {
    openShell(null, $('div.console div.inner').empty(), 0);
  }

  $('div.traceback div.frame').each(function() {
    var
      target = $('pre', this)
        .click(function() {
          sourceButton.click();
        }),
      consoleNode = null, source = null,
      frameID = this.id.substring(6);

    /**
     * Add an interactive console to the frames
     */
    if (EVALEX)
      $('<img src="?__debugger__=yes&cmd=resource&f=console.png">')
        .attr('title', 'Open an interactive python shell in this frame')
        .click(function() {
          consoleNode = openShell(consoleNode, target, frameID);
          return false;
        })
        .prependTo(target);

    /**
     * Show sourcecode
     */
    var sourceButton = $('<img src="?__debugger__=yes&cmd=resource&f=source.png">')
      .attr('title', 'Display the sourcecode for this frame')
      .click(function() {
        if (!sourceView)
          $('h2', sourceView =
            $('<div class="box"><h2>View Source</h2><div class="sourceview">' +
              '<table></table></div>')
              .insertBefore('div.explanation'))
            .css('cursor', 'pointer')
            .click(function() {
              sourceView.slideUp('fast');
            });
        $.get('', {__debugger__: 'yes', cmd:
            'source', frm: frameID, s: SECRET}, function(data) {
          $('table', sourceView)
            .replaceWith(data);
          if (!sourceView.is(':visible'))
            sourceView.slideDown('fast', function() {
              focusSourceBlock();
            });
          else
            focusSourceBlock();
        });
        return false;
      })
      .prependTo(target);
  });

  /**
   * toggle traceback types on click.
   */
  $('h2.traceback').click(function() {
    $(this).next().slideToggle('fast');
    $('div.plain').slideToggle('fast');
  }).css('cursor', 'pointer');
  $('div.plain').hide();

  /**
   * Add extra info (this is here so that only users with JavaScript
   * enabled see it.)
   */
  $('span.nojavascript')
    .removeClass('nojavascript')
    .html('<p>To switch between the interactive traceback and the plaintext ' +
          'one, you can click on the "Traceback" headline.  From the text ' +
          'traceback you can also create a paste of it. ' + (!EVALEX ? '' :
          'For code execution mouse-over the frame you want to debug and ' +
          'click on the console icon on the right side.' +
          '<p>You can execute arbitrary Python code in the stack frames and ' +
          'there are some extra helpers available for introspection:' +
          '<ul><li><code>dump()</code> shows all variables in the frame' +
          '<li><code>dump(obj)</code> dumps all that\'s known about the object</ul>'));

  /**
   * Add the pastebin feature
   */
  $('div.plain form')
    .submit(function() {
      var label = $('input[type="submit"]', this);
      var old_val = label.val();
      label.val('submitting...');
      $.ajax({
        dataType:     'json',
        url:          document.location.pathname,
        data:         {__debugger__: 'yes', tb: TRACEBACK, cmd: 'paste',
                       s: SECRET},
        success:      function(data) {
          $('div.plain span.pastemessage')
            .removeClass('pastemessage')
            .text('Paste created: ')
            .append($('<a>#' + data.id + '</a>').attr('href', data.url));
        },
        error:        function() {
          alert('Error: Could not submit paste.  No network connection?');
          label.val(old_val);
        }
      });
      return false;
    });

  // if we have javascript we submit by ajax anyways, so no need for the
  // not scaling textarea.
  var plainTraceback = $('div.plain textarea');
  plainTraceback.replaceWith($('<pre>').text(plainTraceback.text()));
});


/**
 * Helper function for shell initialization
 */
function openShell(consoleNode, target, frameID) {
  if (consoleNode)
    return consoleNode.slideToggle('fast');
  consoleNode = $('<pre class="console">')
    .appendTo(target.parent())
    .hide()
  var historyPos = 0, history = [''];
  var output = $('<div class="output">[console ready]</div>')
    .appendTo(consoleNode);
  var form = $('<form>&gt;&gt;&gt; </form>')
    .submit(function() {
      var cmd = command.val();
      $.get('', {
          __debugger__: 'yes', cmd: cmd, frm: frameID, s: SECRET}, function(data) {
        var tmp = $('<div>').html(data);
        $('span.extended', tmp).each(function() {
          var hidden = $(this).wrap('<span>').hide();
          hidden
            .parent()
            .append($('<a href="#" class="toggle">&nbsp;&nbsp;</a>')
              .click(function() {
                hidden.toggle();
                $(this).toggleClass('open')
                return false;
              }));
        });
        output.append(tmp);
        command.focus();
        consoleNode.scrollTop(consoleNode.get(0).scrollHeight);
        var old = history.pop();
        history.push(cmd);
        if (typeof old != 'undefined')
          history.push(old);
        historyPos = history.length - 1;
      });
      command.val('');
      return false;
    }).
    appendTo(consoleNode);

  var command = $('<input type="text">')
    .appendTo(form)
    .keydown(function(e) {
      if (e.charCode == 100 && e.ctrlKey) {
        output.text('--- screen cleared ---');
        return false;
      }
      else if (e.charCode == 0 && (e.keyCode == 38 || e.keyCode == 40)) {
        if (e.keyCode == 38 && historyPos > 0)
          historyPos--;
        else if (e.keyCode == 40 && historyPos < history.length)
          historyPos++;
        command.val(history[historyPos]);
        return false;
      }
    });

  return consoleNode.slideDown('fast', function() {
    command.focus();
  });
}

/**
 * Focus the current block in the source view.
 */
function focusSourceBlock() {
  var tmp, line = $('table.source tr.current');
  for (var i = 0; i < 7; i++) {
    tmp = line.prev();
    if (!(tmp && tmp.is('.in-frame')))
      break
    line = tmp;
  }
  var container = $('div.sourceview');

  container.scrollTop(line.offset().top - container.offset().top + container.scrollTop());
}
