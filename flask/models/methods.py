from flask.templating import render_template


class Router():

	def __init__(self,app):
		self.app = app

	def get(self,path,function=None,html=None):
		if function == None:
			func = lambda **kw:render_template(str(html),**kw)
			if self.app.view_functions.get(html):
				func = self.app.view_functions.get(html)

			self.app.add_url_rule(path,html,func,methods=["GET"])

		else:
			self.app.add_url_rule( path,function.__name__,function,methods=["GET"])
	

	def post(self,path,function):
		self.app.add_url_rule(path,function.__name__,function,methods=["POST"])

	def put(self,path,function):
		self.app.add_url_rule( path, function.__name__, function, methods=["PUT"])

	def delete(self,path,function):
		self.app.add_url_rule( path, function.__name__, function, methods=["DELETE"])

