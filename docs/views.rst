.. _views:

Pluggable Views
===============

.. versionadded:: 0.7

Flask 0.7 introduces pluggable views inspired by the generic views from
Django which are based on classes instead of functions.  The main
intention is that you can replace parts of the implementations and this
way have customizable pluggable views.

Basic Principle
---------------

Consider you have a function that loads a list of objects from the
database and renders into a template::

    @app.route('/users/')
    def show_users(page):
        users = User.query.all()
        return render_template('users.html', users=users)

This is simple and flexible, but if you want to provide this view in a
generic fashion that can be adapted to other models and templates as well
you might want more flexibility.  This is where pluggable class based
views come into place.  As the first step to convert this into a class
based view you would do this::


    from flask.views import View

    class ShowUsers(View):

        def dispatch_request(self):
            users = User.query.all()
            return render_template('users.html', objects=users)

    app.add_url_rule('/users/', ShowUsers.as_view('show_users'))

As you can see what you have to do is to create a subclass of
:class:`flask.views.View` and implement
:meth:`~flask.views.View.dispatch_request`.  Then we have to convert that
class into an actual view function by using the
:meth:`~flask.views.View.as_view` class method.  The string you pass to
that function is the name of the endpoint that view will then have.  But
this by itself is not helpful, so let's refactor the code a bit::

    
    from flask.views import View

    class ListView(View):

        def get_template_name(self):
            raise NotImplementedError()

        def render_template(self, context):
            return render_template(self.get_template_name(), **context)

        def dispatch_request(self):
            context = {'objects': self.get_objects()}
            return self.render_template(context)

    class UserView(ListView):

        def get_template_name(self):
            return 'users.html'

        def get_objects(self):
            return User.query.all()

This of course is not that helpful for such a small example, but it's good
enough to explain the basic principle.  When you have a class based view
the question comes up what `self` points to.  The way this works is that
whenever the request is dispatched a new instance of the class is created
and the :meth:`~flask.views.View.dispatch_request` method is called with
the parameters from the URL rule.  The class itself is instanciated with
the parameters passed to the :meth:`~flask.views.View.as_view` function.
For instance you can write a class like this::

    class RenderTemplateView(View):
        def __init__(self, template_name):
            self.template_name = template_name
        def dispatch_request(self):
            return render_template(self.template_name)

And then you can register it like this::

    app.add_url_view('/about', RenderTemplateView.as_view(
        'about_page', template_name='about.html'))

Method Hints
------------

Pluggable views are attached to the application like a regular function by
either using :func:`~flask.Flask.route` or better
:meth:`~flask.Flask.add_url_rule`.  That however also means that you would
have to provide the names of the HTTP methods the view supports when you
attach this.  In order to move that information to the class you can
provide a :attr:`~flask.views.View.methods` attribute that has this
information::

    class MyView(View):
        methods = ['GET', 'POST']

        def dispatch_request(self):
            if request.method == 'POST':
                ...
            ...

    app.add_url_view('/myview', MyView.as_view('myview'))

Method Based Dispatching
------------------------

For RESTful APIs it's especially helpful to execute a different function
for each HTTP method.  With the :class:`flask.views.MethodView` you can
easily do that.  Each HTTP method maps to a function with the same name
(just in lowercase)::

    from flask.views import MethodView

    class UserAPI(MethodView):

        def get(self):
            users = User.query.all()
            ...

        def post(self):
            user = User.from_form_data(request.form)
            ...

    app.add_url_view('/users/', UserAPI.as_view('users'))

That way you also don't have to provide the
:attr:`~flask.views.View.methods` attribute.  It's automatically set based
on the methods defined in the class.
