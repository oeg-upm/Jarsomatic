# Jarsomatic

An application to run jar when a specific file(s) are changed on a repo in Github


Collaborators: Daniel Garijo (@dgarijo)


###Configuration file:
The configuration file should be named *jarsomatic.cfg* and located in the top level of Jarsomatic folder

a sample configuration file is below
```
[DEFAULT]
watch: OnToology/target.csv, "OnToology/alojamiento.xml"
[JAR]
location: /home/ahmad/target
command: java my.java -a -lang english

```

###Deployment
For using wsgi you can update jarsomatic.wsgi according to your server settings
[Apache with WSGI](http://flask.pocoo.org/docs/0.10/deploying/mod_wsgi/)

Or you can use any of the deployment options mentioned in Flask official website [Here](http://flask.pocoo.org/docs/0.10/deploying/)




