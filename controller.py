#!/usr/bin/env python

import glob
import operator, os, pickle, sys
import cherrypy

from formencode import Invalid
from n3wbl0g.lib import template
from n3wbl0g.form import LinkForm, CommentForm
from n3wbl0g.model import Link, Comment
from genshi.filters import HTMLFormFiller
from cherrypy.lib import static
from cherrypy.lib.static import serve_file

net_config = {'server.socket_host': '207.12.89.17' 
               ,'server.socket_port': 80}

cherrypy.config.update(net_config)     



class Root(object):

    def __init__(self, data):
        self.data = data

    @cherrypy.expose
    @template.output('index.html')
    def index(self):
        links = sorted(self.data.values(), key=operator.attrgetter('time'), reverse=True)
        return template.render(links=links)

    @cherrypy.expose
    @template.output('submit.html')
    def submit(self, cancel=False, **data):
        if cherrypy.request.method == 'POST':
            if cancel:
                raise cherrypy.HTTPRedirect('/')
            form = LinkForm()
            try:
                data = form.to_python(data)
                link = Link(**data)
                self.data[link.id] = link
                raise cherrypy.HTTPRedirect('/')
            except Invalid, e:
                errors = e.unpack_errors()
        else:
            errors = {}

        return template.render(errors=errors) | HTMLFormFiller(data=data)
    	
    @cherrypy.expose
    @template.output('info.html')
    def info(self, id):
        link = self.data.get(id)
        if not link:
            raise cherrypy.NotFound()
        return template.render(link=link)
	
    @cherrypy.expose
    @template.output('comment.html')
    def comment(self, id, cancel=False, **data):
        link = self.data.get(id)
        if not link:
            raise cherrypy.NotFound()
        if cherrypy.request.method == 'POST':
            if cancel:
                raise cherrypy.HTTPRedirect('/info/%s' % link.id)
            form = CommentForm()
            try:
                data = form.to_python(data)
                comment = link.add_comment(**data)
                raise cherrypy.HTTPRedirect('/info/%s' % link.id)
            except Invalid, e:
                errors = e.unpack_errors()
        else:
            errors = {}

        return template.render(link=link, comment=None,
                               errors=errors) | HTMLFormFiller(data=data)

    @cherrypy.expose
    @template.output('tutorials.html')
    def tutorials(self):
        return template.render() 

    @cherrypy.expose
    @template.output('blog.html')
    def blog(self):
        return template.render() 

    @cherrypy.expose
    @template.output('interesting.html')
    def interesting(self):
        return template.render() 

    @cherrypy.expose
    @template.output('join.html')
    def join(self):
        return template.render() 
    
    @cherrypy.expose
    @template.output('downloads.html')
    def downloads(self, directory="."):
	filepath = []
        stuff = []
        for filename in glob.glob(directory + '/n3wbl0g/downloadable/*'):
            absPath = os.path.abspath(filename)
            filepath.append(os.path.basename(filename))
	    stuff.append(absPath)
        return template.render(stuff=stuff, filepath=filepath)
    
    @cherrypy.expose 
    def download(self, filepath):
	return serve_file(filepath, "application/x-download", "attachment")


def main(filename):
    # load data from the pickle file, or initialize it to an empty list
    if os.path.exists(filename):
        fileobj = open(filename, 'rb')
        try:
            data = pickle.load(fileobj)
        finally:
            fileobj.close()
    else:
        data = {}

    def _save_data():
        # save data back to the pickle file
        fileobj = open(filename, 'wb')
        try:
            pickle.dump(data, fileobj)
        finally:
            fileobj.close()
    if hasattr(cherrypy.engine, 'subscribe'): # CherryPy >= 3.1
        cherrypy.engine.subscribe('stop', _save_data)
    else:
        cherrypy.engine.on_stop_engine_list.append(_save_data)





    # Some global configuration; note that this could be moved into a
    # configuration file
    cherrypy.config.update({
        'tools.encode.on': True, 'tools.encode.encoding': 'utf-8',
        'tools.decode.on': True,
        'tools.trailing_slash.on': True,
        'tools.staticdir.root': os.path.abspath(os.path.dirname(__file__)),
    })

    cherrypy.quickstart(Root(data), '/', {
        '/media': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'static'
        }
    })

if __name__ == '__main__':
    main(sys.argv[1])
