from ansible import errors
from ansible import utils
from ansible.callbacks import vv

class CallbackModule(object):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'injection'
    CALLBACK_NAME = 'bootstrap'

    invocation_defaults = {
        'module_name':          "",
        'module_args':          "",
        'module_complex_args':  {},
    }

    def __init__(self):
        pass

    def runner_on_failed(self, *args, **kwargs):
        return self._on_any(*args, **kwargs)

    def runner_on_ok(self, *args, **kwargs):
        return self._on_any(*args, **kwargs)

    def _on_any(self, host, result, *args, **kwargs):
        cleaned_invocation = result.get('cleaned_invocation', None)

        if cleaned_invocation is not None:
            for key, value in self.invocation_defaults.iteritems():
                cleaned_item = cleaned_invocation.get(key, value)
                result['invocation'][key] = cleaned_item
            try:
                del(result['cleaned_invocation'])
            except KeyError:
                pass
