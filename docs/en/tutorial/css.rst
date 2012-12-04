.. _tutorial-css:

Step 7: Adding Style
====================

Now that everything else works, it's time to add some style to the
application.  Just create a stylesheet called `style.css` in the `static`
folder we created before:

.. sourcecode:: css

    body            { font-family: sans-serif; background: #eee; }
    a, h1, h2       { color: #377BA8; }
    h1, h2          { font-family: 'Georgia', serif; margin: 0; }
    h1              { border-bottom: 2px solid #eee; }
    h2              { font-size: 1.2em; }

    .page           { margin: 2em auto; width: 35em; border: 5px solid #ccc;
                      padding: 0.8em; background: white; }
    .entries        { list-style: none; margin: 0; padding: 0; }
    .entries li     { margin: 0.8em 1.2em; }
    .entries li h2  { margin-left: -1em; }
    .add-entry      { font-size: 0.9em; border-bottom: 1px solid #ccc; }
    .add-entry dl   { font-weight: bold; }
    .metanav        { text-align: right; font-size: 0.8em; padding: 0.3em;
                      margin-bottom: 1em; background: #fafafa; }
    .flash          { background: #CEE5F5; padding: 0.5em;
                      border: 1px solid #AACBE2; }
    .error          { background: #F0D6D6; padding: 0.5em; }

Continue with :ref:`tutorial-testing`.
