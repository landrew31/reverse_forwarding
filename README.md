### Description
This service is for accepting requests from remote services on your local machine during debuging. Common case - testing integration with payment providers.
### How it works
Application creates 2 processes and instance of `multiprocessing.Array` for communication between processes. In first of them app establishes ssh connection with service serveo.net for reverse forwarding. Then we parse remote origin, given us by servo.net and save it into created array. In the other process app for sending remote origin and redirecting requests is launched.

### Integration
By default service is running on `localhost:9090`. In your main application you must get remote origin from the service to send it to needed remote application which can send request to your local app. Also, during getting remote origin, you acknowledge the service, that it has forward requests from remote to concrete local app and only requests on concrete url. To get remote origin for your local app, send `POST` request to the reverse forvarding service on url `/proxify_link` with required body parametr `url` on which you want to accept remote requests.
Here is example of implementation on `Python`:
```
import json
import requests
from urlparse import urlparse

class RemoteUrlForwarder(object):
    _url = get_config('reverse_forwarding_link')

    def _post(self, url_to_forward):
        try:
            response = requests.post(
                url=self._url,
                data=json.dumps({'url': url_to_forward}),
            )
            return json.loads(response.content)
        except Exception:
            return {}

    def _is_configured(self):
        return self._url is not None

    def get_remote_link_to_localhost(self, url_to_forward):
        if not self._is_configured():
            return url_to_forward

        data = self._post(url_to_forward)
        remote_origin = data.get('proxy_hostname')
        if not remote_origin:
            return url_to_forward

        parsed = urlparse(url_to_forward)
        local_origin = '%s://%s' % (parsed.scheme, parsed.netloc)
        return '%s%s' % (remote_origin, url_to_forward[len(local_origin):])
```

### Running

##### 0. Install `pyenv`.
If you have pyenv on your computer, skip this step. Otherwise, follow next:

- Execute in terminal
    >`curl -L https://raw.githubusercontent.com/pyenv/pyenv-installer/master/bin/pyenv-installer | bash`
- Add lines in ~/.bashrc:
    >`export PATH="~/.pyenv/bin:$PATH"`
    >`eval "$(pyenv init -)"`
    >`eval "$(pyenv virtualenv-init -)"`
- Execute in terminal:
    >`exec bash`
- Execute in terminal:
    >`pyenv update`

##### 1. Create `virtualenv`:
Create `virtualenv` using `pyenv`:
- Install appropriate version of `python`:
    >`pyenv install 3.6.4`
- Create `virtualenv` named `reverse_forwarding`:
    >`pyenv virtualenv 3.6.4 reverse_forwarding`

##### 2. Clone project:
- Execute being in your workspace directory:
    >`git clone https://github.com/landrew31/reverse_forwarding.git`

##### 3. Run service:
Run beeing in project path.
- Launch `virtualenv` if needed:
    >`pyenv local reverse_forwarding`
- Run:
    >`python3 app.py`
