# Zenoss-5.0.x JSON API Example (python)
#
# To quickly explore, execute 'python -i api_example.py'
#
# >>> z = ZenossAPI()
# >>> events = z.get_events()
# etc.

import json
import pycurl
from StringIO import StringIO

# must have just the hostname and not the vhost
ZENOSS_INSTANCE = 'https://jhanson-desktop'
ZENOSS_USERNAME = 'admin'
ZENOSS_PASSWORD = 'zenoss'
ZENOSS_VHOST = "zenoss5"
ROUTERS = { 'MessagingRouter': 'messaging',
            'EventsRouter': 'evconsole',
            'ProcessRouter': 'process',
            'ServiceRouter': 'service',
            'DeviceRouter': 'device',
            'NetworkRouter': 'network',
            'TemplateRouter': 'template',
            'DetailNavRouter': 'detailnav',
            'ReportRouter': 'report',
            'MibRouter': 'mib',
            'ZenPackRouter': 'zenpack' }

class ZenossAPI():
    def __init__(self, debug=False):
        """
        Initialize the API connection, log in, and store authentication cookie
        """
        self.reqCount = 0
        pass

    def _router_request(self, router, method, data=[]):
        if router not in ROUTERS:
            raise Exception('Router "' + router + '" not available.')
        url = ZENOSS_INSTANCE + '/zport/dmd/' + ROUTERS[router] + '_router'
        creds = "%s:%s" %( ZENOSS_USERNAME, ZENOSS_PASSWORD)
        # Convert the request parameters into JSON
        reqData = json.dumps([dict(
                    action=router,
                    method=method,
                    data=data,
                    type='rpc',
                    tid=self.reqCount)])

        # Contruct a standard URL request for API calls
        buffer = StringIO()
        c = pycurl.Curl()
        c.setopt(pycurl.URL, url)
        c.setopt(pycurl.USERPWD, creds)
        # zenoss uses self signed certs so we can not verify them
        c.setopt(pycurl.SSL_VERIFYHOST, 0)
        c.setopt(pycurl.SSL_VERIFYPEER, 0)
        c.setopt(pycurl.POST, 1)
        c.setopt(pycurl.HTTPHEADER, ['Content-type: application/json', 'Host: %s' % ZENOSS_VHOST])
        c.setopt(pycurl.POSTFIELDS, reqData)
        c.setopt(c.WRITEDATA, buffer)
        c.perform()
        c.close()
        body = buffer.getvalue()
        # Increment the request count ('tid'). More important if sending multiple
        # calls in a single request
        self.reqCount += 1
        return json.loads(body)

    def get_devices(self, deviceClass='/zport/dmd/Devices'):
        return self._router_request('DeviceRouter', 'getDevices',
                                    data=[{'uid': deviceClass}])['result']

    def get_events(self, device=None, component=None, eventClass=None):
        data = dict(start=0, limit=100, dir='DESC', sort='severity')
        data['params'] = dict(severity=[5,4,3,2], eventState=[0,1])

        if device: data['params']['device'] = device
        if component: data['params']['component'] = component
        if eventClass: data['params']['eventClass'] = eventClass

        return self._router_request('EventsRouter', 'query', [data])['result']

    def add_device(self, deviceName, deviceClass):
        data = dict(deviceName=deviceName, deviceClass=deviceClass)
        return self._router_request('DeviceRouter', 'addDevice', [data])

    def create_event_on_device(self, device, severity, summary):
        if severity not in ('Critical', 'Error', 'Warning', 'Info', 'Debug', 'Clear'):
            raise Exception('Severity "' + severity +'" is not valid.')

        data = dict(device=device, summary=summary, severity=severity,
                    component='', evclasskey='', evclass='')
        return self._router_request('EventsRouter', 'add_event', [data])

if __name__ == '__main__':
    z = ZenossAPI()
    from pprint import pprint
    pprint(z.get_devices())
