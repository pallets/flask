import os,importlib as lib,flask


class Controllers():

	def __init__(self,App):
		self.Controll = {}
		for  i in os.listdir("Controller"):
			if not i.startswith("__"):
				model = i.strip(".py")
				Cl = lib.import_module("Controller.%s"%model,model)
				try:
					self.Controll.update({model:getattr(Cl,model)(App)})
				except AttributeError:
					self.Controll.update({model:Cl})
		
	def __getattr__(self,k):
		return self.Controll.get(k)

	def __dir__(self):
		return self.Controll.keys()


class model():
	def __init__(self):
		self.moduls = {}
		for  i in dir(flask):
			if not i.startswith("__"):
				model = i.strip(".py")
				try:
					self.moduls.update({model:getattr(flask,model)})
				except:
					pass
		
	def __getattr__(self,k):
		return self.moduls.get(k)

	def __dir__(self):
		return self.moduls.keys()


class Moduls():

	def __init__(self):
		self.moduls = {}
		for  i in os.listdir("model"):
			if not i.startswith("__"):
				model = i.strip(".py")
				Cl = lib.import_module("model.%s"%model,model)
				try:
					self.moduls.update({model:getattr(Cl,model)})
				except AttributeError:
					self.moduls.update({model:Cl})
				except:
					pass
		
	def __getattr__(self,k):
		return self.moduls.get(k)

	def __dir__(self):
		return self.moduls.keys()
