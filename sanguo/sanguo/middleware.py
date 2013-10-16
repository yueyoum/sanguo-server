import struct

from django.http import HttpResponse


NUM_FIELD = struct.Struct('>i')

class PackMessageData(object):
    def process_response(self, request, response):
        if response.status_code != 200:
            return response

        # TODO get other messages
        other_msgs = []
        num_of_msgs = len(other_msgs) + 1

        data = '%s%s%s' % (
                NUM_FIELD.pack(num_of_msgs),
                response.content,
                ''.join(other_msgs)
                )

        return HttpResponse(data, content_type='text/plain')


