Contributing
============

See the Pallets `detailed contributing documentation <contrib_>`_ for many ways
to contribute, including reporting issues, requesting features, asking or
answering questions, and making PRs.

.. _contrib: https://palletsprojects.com/contributing/

Copy-to-Clipboard Buttons
-------------------------

The Flask docs are built with Sphinx. Follow the steps below to add a copy
button to every code block by using the ``sphinx-copybutton`` extension.

.. versionchanged:: 3.2
   Added copy button setup instructions for the documentation build.

1. Install the extension in your activated virtual environment:

   .. code-block:: console

      (venv) $ pip install sphinx-copybutton

   If you keep documentation dependencies in ``pyproject.toml`` (group
   ``docs``) or another requirements file, add ``sphinx-copybutton`` there and
   regenerate any lock files (for example ``uv lock``) so other contributors get
   the dependency automatically.

2. Enable the extension in ``docs/conf.py`` by appending it to
   ``extensions``:

   .. code-block:: python

      extensions = [
          "sphinx.ext.autodoc",
          "sphinx.ext.extlinks",
          "sphinx.ext.intersphinx",
          "sphinx_copybutton",
          "sphinxcontrib.log_cabinet",
          "sphinx_tabs.tabs",
          "pallets_sphinx_themes",
      ]

3. (Optional) Strip interactive prompts from the copied text so readers get
   clean commands. Add the following configuration near the bottom of the
   general settings in ``docs/conf.py``:

   .. code-block:: python

      copybutton_prompt_text = r">>> |\.\.\. |\$ "
      copybutton_prompt_is_regexp = True
      copybutton_only_copy_prompt_lines = False

   Tweak ``copybutton_prompt_text`` if your docs use different prompt strings.

4. Build the documentation locally to confirm everything works:

   .. code-block:: console

      (venv) $ make html

   This runs ``sphinx-build`` via the docs ``Makefile`` and places HTML under
   ``docs/_build/html``. Resolve any warnings or errors before committing.

5. Test the copy button in the generated site. Open the landing page in your
   browser (macOS example shown):

   .. code-block:: console

      (venv) $ open docs/_build/html/index.html

   Hover over any code block—each one now shows a copy icon. Click the icon,
   paste into a terminal or editor, and verify that prompts such as ``>>>`` and
   ``$`` were stripped if you enabled the regex configuration.

Best Practices
~~~~~~~~~~~~~~

* Run ``make clean`` (or delete ``docs/_build``) when you switch branches to
  avoid stale artifacts.
* Consider ``SPHINXOPTS=-W make html`` to treat warnings as errors and keep the
  docs healthy.
* Use ``sphinx-autobuild`` for faster authoring loops: ``uv run -m sphinx_autobuild docs docs/_build/dirhtml``.
* Preview multiple sections after theme or JavaScript changes to ensure the copy
  button renders consistently everywhere.
