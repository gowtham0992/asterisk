"""Unpack the fixed preparation handoff in memory, without trusting its claims."""
import io
import stat
import zipfile
import zlib

NAMES={'splits.csv','entities.csv','asterisk.json','preparation-review.json','README.md'}


def unpack(data):
    if not data or len(data)>18_000_000:
        raise ValueError('Prepared ZIP exceeds the 18 MB upload limit.')
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            members=archive.infolist()
            if len(members)!=len(NAMES) or {m.filename for m in members}!=NAMES:
                raise ValueError('Choose the prepared-input ZIP exported by Asterisk; its five original files are required.')
            if sum(m.file_size for m in members)>16_000_000:
                raise ValueError('Expanded prepared files exceed 16 MB.')
            result=[]
            for member in members:
                if (member.file_size>10_000_000 or member.flag_bits&1 or
                    member.compress_type not in (zipfile.ZIP_STORED,zipfile.ZIP_DEFLATED) or
                    stat.S_IFMT(member.external_attr>>16) not in (0,stat.S_IFREG)):
                    raise ValueError('Unsupported or oversized prepared ZIP entry.')
                with archive.open(member) as stream:
                    raw=stream.read(10_000_001)
                if len(raw)>10_000_000 or len(raw)!=member.file_size:
                    raise ValueError('Prepared ZIP entry exceeds its bounds.')
                result.append({'name':member.filename,'content':raw.decode('utf-8')})
            return result
    except (zipfile.BadZipFile,UnicodeError,RuntimeError,NotImplementedError,EOFError,zlib.error) as exc:
        raise ValueError('Prepared ZIP is damaged, unsupported, or contains invalid UTF-8.') from exc
