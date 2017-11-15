# Jarsomatic

An application to run jar when a specific file(s) are changed on a repo in Github


Collaborators: Daniel Garijo (@dgarijo), Ahmad Alobaid

### Diagram: 
![Image](../master/Jarsomatic Diagram.png?raw=true)


## How to use it
1. Add the url of the webhook.
2. Add jar.cfg.
3. After that, when ever you do a push to the master branch, if one of files you are watching is changed, then it will
be triggered and the command you specified will be called.


### JAR Configuration file:
There should a configuration file per monitored JAR (should be named jar.cfg)
```
[DEFAULT]
watch: "dir1/file1.owl", dir2/file2.csv
command: ls
```


### Jarsomatic Configuration file:
The configuration file should be named *jarsomatic.cfg* and located in the top level of Jarsomatic folder

a sample configuration file is below
```
[DEFAULT]
tmp: /tmp
[GITHUB]
token: xxxxxxxxxxxxxxxxxx

```


### Automatic deployment with Jarsomatic
To do so, the recommended way is to use access token

1. create access token [how to](https://github.com/blog/1509-personal-api-tokens)
2. git clone https://<token>@github.com/owner/repo.git


### Deployment
For using wsgi you can update jarsomatic.wsgi according to your server settings
[Apache with WSGI](http://flask.pocoo.org/docs/0.10/deploying/mod_wsgi/)

Or you can use any of the deployment options mentioned in Flask official website [Here](http://flask.pocoo.org/docs/0.10/deploying/)




