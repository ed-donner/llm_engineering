from my_pkg.lib import has_gpu


def test_torch_cuda():
    assert has_gpu()
