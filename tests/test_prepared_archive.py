import io,json,stat,zipfile
import pytest
from app.prepared_archive import unpack,NAMES
from tests.test_api import client,HEADERS


def package(changes=None):
    files={name:b'text' for name in NAMES};files.update(changes or {})
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        for name,value in files.items():z.writestr(name,value)
    return out.getvalue()


def test_preserves_unicode_bom_and_line_endings():
    original='\ufeffsample,partition\r\nα,train\r\n'
    files={f['name']:f['content'] for f in unpack(package({'splits.csv':original.encode()}))}
    assert files['splits.csv']==original


@pytest.mark.parametrize('extra',['../splits.csv','nested/data.csv','.env','other.py'])
def test_extra_or_unsafe_paths_are_rejected(extra):
    with pytest.raises(ValueError,match='five'):unpack(package({extra:b'x'}))


def test_symlink_and_duplicate_names_rejected():
    for mode in ['symlink','duplicate']:
        out=io.BytesIO()
        with zipfile.ZipFile(out,'w') as z:
            for name in NAMES:
                info=zipfile.ZipInfo(name)
                if mode=='symlink' and name=='splits.csv':info.external_attr=(stat.S_IFLNK|0o777)<<16
                z.writestr(info,b'x')
            if mode=='duplicate':
                with pytest.warns(UserWarning):z.writestr('splits.csv',b'x')
        with pytest.raises(ValueError):unpack(out.getvalue())


def test_compressed_oversize_and_invalid_utf8_rejected():
    with pytest.raises(ValueError,match='oversized'):unpack(package({'splits.csv':b'x'*10_000_001}))
    with pytest.raises(ValueError,match='UTF-8'):unpack(package({'splits.csv':b'\xff'}))
    with pytest.raises(ValueError):unpack(b'not a zip')


def test_route_requires_session_csrf_and_zip_content_type(client):
    data=package()
    url='/api/investigations/import-prepared'
    assert client.post(url,content=data).status_code==403
    assert client.post(url,content=data,headers=HEADERS).status_code==415
    headers={**HEADERS,'Content-Type':'application/zip'}
    assert client.post(url,content=data,headers={**headers,'Origin':'https://other.invalid'}).status_code==403
    response=client.post(url,content=data,headers=headers)
    assert response.status_code==200 and len(response.json()['files'])==5
    client.cookies.clear()
    assert client.post(url,content=data,headers=headers).status_code==401
