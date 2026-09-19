"""Deployment boundary for a small, invitation-only research preview."""
import base64
import os
import secrets
from dataclasses import dataclass

@dataclass(frozen=True)
class ReleaseSettings:
    public: bool
    hosts: tuple[str, ...]
    password: str

    @classmethod
    def from_env(cls):
        public=os.getenv('ASTERISK_PUBLIC','0')=='1'
        hosts=tuple(h.strip() for h in os.getenv('ASTERISK_ALLOWED_HOSTS','127.0.0.1,localhost,testserver').split(',') if h.strip())
        password=os.getenv('ASTERISK_PREVIEW_PASSWORD','')
        if public and (len(password)<24 or not hosts or any('*' in h for h in hosts)):
            raise RuntimeError('Public preview requires an explicit host allowlist and a password of at least 24 characters.')
        return cls(public,hosts,password)

    def authorized(self,header):
        if not self.public:return True
        try:
            scheme,value=header.split(' ',1)
            if scheme.lower()!='basic':return False
            username,password=base64.b64decode(value,validate=True).decode().split(':',1)
        except (ValueError,UnicodeError):return False
        return secrets.compare_digest(username.encode(),b'reviewer') and secrets.compare_digest(password.encode(),self.password.encode())
