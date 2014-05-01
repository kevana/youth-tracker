#!flask/bin/python
from flask import Flask, jsonify, abort, request, make_response, url_for
from flask.ext.httpauth import HTTPBasicAuth

import json

app = Flask(__name__, static_url_path = "")
auth = HTTPBasicAuth()
 
@auth.get_password
def get_password(username):
    '''Used by Flask-HTTPAuth, return password for user.'''
    if username == 'kevan':
        return 'password'
    return None
 
@auth.error_handler
def unauthorized():
    '''Return 403 Unauthorized error.'''
    return make_response(jsonify( { 'error': 'Unauthorized access' } ), 403)
    # return 403 instead of 401 to prevent browsers from displaying the default auth dialog
    
@app.errorhandler(400)
def not_found(error):
    '''Return 400 Bad request error.'''
    return make_response(jsonify( { 'error': 'Bad request' } ), 400)
 
@app.errorhandler(404)
def not_found(error):
    '''Return 404 Not found error.'''
    return make_response(jsonify( { 'error': 'Not found' } ), 404)
 
events = []

class ObjectBase:
    '''Base object for json-serializable classes.'''
    def to_json(self):
        '''Recursively dump object to json.'''
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    def __init__(self):
        '''Add the object id to its __dict__.'''
        self.id = id(self)

class Event(ObjectBase):
    '''Events that have destroyed my youthful optimism.'''
    def __init__(self, title="", description="", youth=""):
        '''Init class with values.'''
        self.id = id(self)
        self.title = title
        self.description = description
        self.youth = youth

class Hook(ObjectBase):
    '''Hooks for new event creation.'''
    def __init__(self, url=""):
        self.id = id(self)
        self.url = url


def make_public_event(event):
    '''Return event with id field replaced with URI.'''
    old_event = event.__dict__
    new_event = {}
    for field in old_event:
        if field == 'id':
            new_event['uri'] = url_for('get_event', event_id = old_event['id'], _external = True)
        else:
            new_event[field] = old_event[field]
    return new_event
    
@app.route('/youth-tracker/api/v1.0/events', methods = ['GET'])
def get_events():
    '''Return list of all events.'''
    return jsonify( { 'events': map(make_public_event, events) } )
 
@app.route('/youth-tracker/api/v1.0/events/<int:event_id>', methods = ['GET'])
def get_event(event_id):
    '''Return event with id:event_id or 404 if not found.'''
    event = filter(lambda t: t['id'] == event_id, events)
    if len(event) == 0:
        abort(404)
    return jsonify( { 'event': make_public_event(event[0]) } )
 
@app.route('/youth-tracker/api/v1.0/events', methods = ['POST'])
@auth.login_required
def create_event():
    '''Create new event from request and return new resource.'''
    if not request.json or not 'title' in request.json:
        abort(400)
    event = Event(title=request.json['title'],
                  description=request.json.get('description', ""),
                  youth=request.json.get('youth', ""))
    events.append(event)
    return jsonify( { 'event': make_public_event(event) } ), 201, {'Location': url_for('get_event', event_id=event.id)}
 
@app.route('/youth-tracker/api/v1.0/events/<int:event_id>', methods = ['PUT'])
@auth.login_required
def update_event(event_id):
    '''Update existing event.'''
    event = filter(lambda t: t.id == event_id, events)
    if len(event) == 0:
        abort(404)
    if not request.json:
        abort(400)
    if 'title' in request.json and type(request.json['title']) != unicode:
        abort(400)
    if 'description' in request.json and type(request.json['description']) is not unicode:
        abort(400)
    if 'youth' in request.json and type(request.json['youth']) is not bool:
        abort(400)
    event[0].title = request.json.get('title', event[0].title)
    event[0].description = request.json.get('description', event[0].description)
    event[0].youth = request.json.get('youth', event[0].youth)
    return jsonify( { 'event': make_public_event(event[0]) } )
    
@app.route('/youth-tracker/api/v1.0/events/<int:event_id>', methods = ['DELETE'])
@auth.login_required
def delete_event(event_id):
    '''Delete existing event.'''
    event = filter(lambda t: t.id == event_id, events)
    if len(event) == 0:
        abort(404)
    events.remove(event[0])
    return jsonify( { 'result': True } )
    
if __name__ == '__main__':
    app.run(debug = True)
