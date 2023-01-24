Class-based Views
=================

.. currentmodule:: flask.views

This page introduces using the :class:`View` and :class:`MethodView`
classes to write class-based views.

A class-based view is a class that acts as a view function. Because it
is a class, different instances of the class can be created with
different arguments, to change the behavior of the view. This is also
known as generic, reusable, or pluggable views.

An example of where this is useful is defining a class that creates an
API based on the database model it is initialized with.

For more complex API behavior and customization, look into the various
API extensions for Flask.


Basic Reusable View
-------------------

Let's walk through an example converting a view function to a view
class. We start with a view function that queries a list of users then
renders a template to show the list.

.. code-block:: python

    @app.route("/users/")
    def user_list():
        users = User.query.all()
        return render_template("users.html", users=users)

This works for the user model, but let's say you also had more models
that needed list pages. You'd need to write another view function for
each model, even though the only thing that would change is the model
and template name.

Instead, you can write a :class:`View` subclass that will query a model
and render a template. As the first step, we'll convert the view to a
class without any customization.

.. code-block:: python

    from flask.views import View

    class UserList(View):
        def dispatch_request(self):
            users = User.query.all()
            return render_template("users.html", objects=users)

    app.add_url_rule("/users/", view_func=UserList.as_view("user_list"))

The :meth:`View.dispatch_request` method is the equivalent of the view
function. Calling :meth:`View.as_view` method will create a view
function that can be registered on the app with its
:meth:`~flask.Flask.add_url_rule` method. The first argument to
``as_view`` is the name to use to refer to the view with
:func:`~flask.url_for`.

.. note::

    You can't decorate the class with ``@app.route()`` the way you'd
    do with a basic view function.

Next, we need to be able to register the same view class for different
models and templates, to make it more useful than the original function.
The class will take two arguments, the model and template, and store
them on ``self``. Then ``dispatch_request`` can reference these instead
of hard-coded values.

.. code-block:: python

    class ListView(View):
        def __init__(self, model, template):
            self.model = model
            self.template = template

        def dispatch_request(self):
            items = self.model.query.all()
            return render_template(self.template, items=items)

Remember, we create the view function with ``View.as_view()`` instead of
creating the class directly. Any extra arguments passed to ``as_view``
are then passed when creating the class. Now we can register the same
view to handle multiple models.

.. code-block:: python

    app.add_url_rule(
        "/users/",
        view_func=ListView.as_view("user_list", User, "users.html"),
    )
    app.add_url_rule(
        "/stories/",
        view_func=ListView.as_view("story_list", Story, "stories.html"),
    )


URL Variables
-------------

Any variables captured by the URL are passed as keyword arguments to the
``dispatch_request`` method, as they would be for a regular view
function.

.. code-block:: python

    class DetailView(View):
        def __init__(self, model):
            self.model = model
            self.template = f"{model.__name__.lower()}/detail.html"

        def dispatch_request(self, id)
            item = self.model.query.get_or_404(id)
            return render_template(self.template, item=item)

    app.add_url_rule(
        "/users/<int:id>",
        view_func=DetailView.as_view("user_detail", User)
    )


View Lifetime and ``self``
--------------------------

By default, a new instance of the view class is created every time a
request is handled. This means that it is safe to write other data to
``self`` during the request, since the next request will not see it,
unlike other forms of global state.

However, if your view class needs to do a lot of complex initialization,
doing it for every request is unnecessary and can be inefficient. To
avoid this, set :attr:`View.init_every_request` to ``False``, which will
only create one instance of the class and use it for every request. In
this case, writing to ``self`` is not safe. If you need to store data
during the request, use :data:`~flask.g` instead.

In the ``ListView`` example, nothing writes to ``self`` during the
request, so it is more efficient to create a single instance.

.. code-block:: python

    class ListView(View):
        init_every_request = False

        def __init__(self, model, template):
            self.model = model
            self.template = template

        def dispatch_request(self):
            items = self.model.query.all()
            return render_template(self.template, items=items)

Different instances will still be created each for each ``as_view``
call, but not for each request to those views.


View Decorators
---------------

The view class itself is not the view function. View decorators need to
be applied to the view function returned by ``as_view``, not the class
itself. Set :attr:`View.decorators` to a list of decorators to apply.

.. code-block:: python

    class UserList(View):
        decorators = [cache(minutes=2), login_required]

    app.add_url_rule('/users/', view_func=UserList.as_view())

If you didn't set ``decorators``, you could apply them manually instead.
This is equivalent to:

.. code-block:: python

    view = UserList.as_view("users_list")
    view = cache(minutes=2)(view)
    view = login_required(view)
    app.add_url_rule('/users/', view_func=view)

Keep in mind that order matters. If you're used to ``@decorator`` style,
this is equivalent to:

.. code-block:: python

    @app.route("/users/")
    @login_required
    @cache(minutes=2)
    def user_list():
        ...


Method Hints
------------

A common pattern is to register a view with ``methods=["GET", "POST"]``,
then check ``request.method == "POST"`` to decide what to do. Setting
:attr:`View.methods` is equivalent to passing the list of methods to
``add_url_rule`` or ``route``.

.. code-block:: python

    class MyView(View):
        methods = ["GET", "POST"]

        def dispatch_request(self):
            if request.method == "POST":
                ...
            ...

    app.add_url_rule('/my-view', view_func=MyView.as_view('my-view'))

This is equivalent to the following, except further subclasses can
inherit or change the methods.

.. code-block:: python

    app.add_url_rule(
        "/my-view",
        view_func=MyView.as_view("my-view"),
        methods=["GET", "POST"],
    )


Method Dispatching and APIs
---------------------------

For APIs it can be helpful to use a different function for each HTTP
method. :class:`MethodView` extends the basic :class:`View` to dispatch
to different methods of the class based on the request method. Each HTTP
method maps to a method of the class with the same (lowercase) name.

:class:`MethodView` automatically sets :attr:`View.methods` based on the
methods defined by the class. It even knows how to handle subclasses
that override or define other methods.

We can make a generic ``ItemAPI`` class that provides get (detail),
patch (edit), and delete methods for a given model. A ``GroupAPI`` can
provide get (list) and post (create) methods.

.. code-block:: python

    from flask.views import MethodView

    class ItemAPI(MethodView):
        init_every_request = False

        def __init__(self, model):
            self.model = model
            self.validator = generate_validator(model)

        def _get_item(self, id):
            return self.model.query.get_or_404(id)

        def get(self, id):
            item = self._get_item(id)
            return jsonify(item.to_json())

        def patch(self, id):
            item = self._get_item(id)
            errors = self.validator.validate(item, request.json)

            if errors:
                return jsonify(errors), 400

            item.update_from_json(request.json)
            db.session.commit()
            return jsonify(item.to_json())

        def delete(self, id):
            item = self._get_item(id)
            db.session.delete(item)
            db.session.commit()
            return "", 204

    class GroupAPI(MethodView):
        init_every_request = False

        def __init__(self, model):
            self.model = model
            self.validator = generate_validator(model, create=True)

        def get(self):
            items = self.model.query.all()
            return jsonify([item.to_json() for item in items])

        def post(self):
            errors = self.validator.validate(request.json)

            if errors:
                return jsonify(errors), 400

            db.session.add(self.model.from_json(request.json))
            db.session.commit()
            return jsonify(item.to_json())

    def register_api(app, model, name):
        item = ItemAPI.as_view(f"{name}-item", model)
        group = GroupAPI.as_view(f"{name}-group", model)
        app.add_url_rule(f"/{name}/<int:id>", view_func=item)
        app.add_url_rule(f"/{name}/", view_func=group)

    register_api(app, User, "users")
    register_api(app, Story, "stories")

This produces the following views, a standard REST API!

================= ========== ===================
URL               Method     Description
----------------- ---------- -------------------
``/users/``       ``GET``    List all users
``/users/``       ``POST``   Create a new user
``/users/<id>``   ``GET``    Show a single user
``/users/<id>``   ``PATCH``  Update a user
``/users/<id>``   ``DELETE`` Delete a user
``/stories/``     ``GET``    List all stories
``/stories/``     ``POST``   Create a new story
``/stories/<id>`` ``GET``    Show a single story
``/stories/<id>`` ``PATCH``  Update a story
``/stories/<id>`` ``DELETE`` Delete a story
================= ========== ===================
