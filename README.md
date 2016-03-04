# Jarsomatic

An application to run jar when a specific file(s) are changed on a repo in Github


Collaborators: Daniel Garijo (@dgarijo), Ahmad Alobaid

###Diagram 
![Image](../master/Jarsomatic Diagram.png?raw=true)




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

###The location of Jarsomatic
In config.py, the value of ```app_home``` need to be changed to the absolute directory of the Jarsomatic folder.
Create file config.py next to jarsomatic.py


###Automatic deployment with Jarsomatic
To do so, the recommended way is to use access token
1. create access token [how to](https://github.com/blog/1509-personal-api-tokens)
2. git clone https://<token>@github.com/owner/repo.git


###Deployment
For using wsgi you can update jarsomatic.wsgi according to your server settings
[Apache with WSGI](http://flask.pocoo.org/docs/0.10/deploying/mod_wsgi/)

Or you can use any of the deployment options mentioned in Flask official website [Here](http://flask.pocoo.org/docs/0.10/deploying/)




