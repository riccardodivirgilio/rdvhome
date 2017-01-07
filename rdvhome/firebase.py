# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from django.utils.functional import cached_property

class Firebase(object):

    @cached_property
    def connection(self):
        from firebase import firebase

        conn = firebase.FirebaseApplication(
            'https://rdvhome-c1afa.firebaseio.com',
            firebase.FirebaseAuthentication(
                'L1qv0FGIh26bE0wPDkXam2Ej2SUWmvR3MyDfF2W1',
                'riccardodivirgilio@gmail.com'
        ))

        return conn

    def get(self, data = None, *args, **kw):
        return self.connection.get('/toggles', data, *args, **kw)

    def post(self, *args, **kw):
        return self.connection.post('/toggles', *args, **kw)

    def put(self, *args, **kw):
        return self.connection.put('/toggles', *args, **kw)

    def delete(self, data = None, *args, **kw):
        return self.connection.delete('/toggles', data, *args, **kw)

storage = Firebase()