# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from django.core.management.base import BaseCommand

from rdvhome.firebase import storage
from rdvhome.toggles import toggles

class Command(BaseCommand):

    def handle(self, **options):

        pks = [obj.id() for obj in toggles]

        for pk in storage.get():
            if not pk in pks:
                self.stdout.write('deleting: %s' % pk)
                storage.delete(pk)

        for toggle in toggles:
            self.stdout.write('updating %s' % toggle.id())
            storage.put(toggle.id(), toggle.serialize())