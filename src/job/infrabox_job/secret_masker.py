import json
import logging
import re


MASK = '****'
MASKING_FAILED = MASK + ' [log redaction unavailable]'


class SecretMasker(object):
    def __init__(self):
        self.values = set()
        self.pattern = None
        self.failed = False

    def add(self, value):
        if self.failed:
            return
        try:
            self._add(value)
        except Exception:
            # Incomplete registration makes all subsequent output unsafe.
            self.failed = True

    def _add(self, value):
        if isinstance(value, dict):
            for item in value.values():
                self.add(item)
            return
        if isinstance(value, list):
            for item in value:
                self.add(item)
            return
        if value is None:
            return

        value = str(value)
        if not value.strip():
            return

        self.values.add(value)
        self.pattern = None
        try:
            structured = json.loads(value)
        except ValueError:
            structured = None

        if isinstance(structured, (dict, list)):
            # Match individual values when a JSON credential is reformatted.
            self.add(structured)
            parts = (value,)
        else:
            # Subprocess output is read one line at a time, including PEM keys.
            parts = (value,) + tuple(line.strip() for line in value.splitlines() if line.strip())
            self.values.update(parts)

        for part in parts:
            self.values.add(json.dumps(part)[1:-1])
            self.values.add(json.dumps(part, ensure_ascii=False)[1:-1])

    def add_sensitive_fields(self, fields):
        try:
            for name, value in fields.items():
                if re.search(r'(password|passwd|secret|token|private[_-]?key|'
                             r'service[_-]?account|access[_-]?key(?:[_-]?id)?)$',
                             name, re.IGNORECASE):
                    self.add(value)
        except Exception:
            self.failed = True

    def mask(self, text):
        if not self.failed:
            try:
                if not self.values:
                    return text
                if self.pattern is None:
                    values = sorted(self.values, key=len, reverse=True)
                    self.pattern = re.compile('|'.join(re.escape(value) for value in values))
                return self.pattern.sub(MASK, text)
            except Exception:
                self.failed = True
        return MASKING_FAILED + ('\n' if text.endswith('\n') else '')


class SecretMaskingFormatter(logging.Formatter):
    def __init__(self, masker, formatter):
        super(SecretMaskingFormatter, self).__init__()
        self.masker = masker
        self.formatter = formatter or logging.Formatter()

    def format(self, record):
        try:
            return self.masker.mask(self.formatter.format(record))
        except Exception:
            # logging.handleError() would print the raw record to stderr.
            self.masker.failed = True
            return MASKING_FAILED
