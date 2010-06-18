.PHONY: deploy

deploy:
	ssh pocoo.org "cd /var/www/flask.pocoo.org/website; sudo -u team git pull origin && sudo /etc/init.d/apache2 reload"
