from tests.test_api import client


def test_benchmark_download_policy_is_pinned_and_does_not_allow_other_hosts(client):
    response = client.get('/')
    policy = response.headers['content-security-policy']
    connect = next(part.strip() for part in policy.split(';') if part.strip().startswith('connect-src'))
    assert connect.split() == [
        'connect-src', "'self'",
        'https://raw.githubusercontent.com/kakumarabhishek/Corrected-Skin-Image-Datasets/ac655ac5a5b93264c57d69d6d520778d915bfc89/DermaMNIST/DermaMNIST_Analysis/',
    ]
    assert "script-src 'self'" in policy
    assert "form-action 'self'" in policy
