"""Deployment boundary for a small, invitation-only research preview."""
import base64
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass(frozen=True)
class ReleaseSettings:
    public: bool
    hosts: tuple[str, ...]
    password: str
    judge_password: str = ''
    judge_until: datetime | None = None

    @classmethod
    def from_env(cls):
        public=os.getenv('ASTERISK_PUBLIC','0')=='1'
        hosts=tuple(h.strip() for h in os.getenv('ASTERISK_ALLOWED_HOSTS','127.0.0.1,localhost,testserver').split(',') if h.strip())
        password=os.getenv('ASTERISK_PREVIEW_PASSWORD','')
        if public and (len(password)<24 or not hosts or any('*' in h for h in hosts)):
            raise RuntimeError('Public preview requires an explicit host allowlist and a password of at least 24 characters.')
        judge_password=os.getenv('ASTERISK_JUDGE_PASSWORD','')
        if judge_password and (len(judge_password)<24 or judge_password==password):
            raise RuntimeError('Judge access needs its own password of at least 24 characters.')
        raw_until=os.getenv('ASTERISK_LADDER_JUDGE_UNTIL','')
        judge_until=datetime.fromisoformat(raw_until) if raw_until else None
        if judge_password and (judge_until is None or judge_until.tzinfo is None):
            raise RuntimeError('Judge credentials require a timezone-aware expiry.')
        return cls(public,hosts,password,judge_password,judge_until)

    def _credentials(self,header):
        try:
            scheme,value=header.split(' ',1)
            if scheme.lower()!='basic':return None
            username,password=base64.b64decode(value,validate=True).decode().split(':',1)
        except (ValueError,UnicodeError):return None
        return username,password

    def is_judge(self,header):
        credentials=self._credentials(header)
        return bool(self.judge_password and self.judge_until and datetime.now(timezone.utc)<self.judge_until and credentials and credentials[0]=='judge'
                    and secrets.compare_digest(credentials[1].encode(),self.judge_password.encode()))

    def authorized(self,header):
        if not self.public:return True
        credentials=self._credentials(header)
        return self.is_judge(header) or bool(credentials and credentials[0]=='reviewer'
            and secrets.compare_digest(credentials[1].encode(),self.password.encode()))
