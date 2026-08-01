# Intentional negative-test clutter — should be flagged by PR reviewer

def test_nothing():
    assert True


def test_also_nothing():
    assert 1 + 1 == 2
