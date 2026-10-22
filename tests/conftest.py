import pytest

from fixtures.fake_embedder import FakeEmbedder
from redteam.victim.datos import cargar_tienda
from redteam.victim.rag import Indice


@pytest.fixture(scope="session")
def tienda():
    return cargar_tienda()


@pytest.fixture(scope="session")
def indice(tienda):
    return Indice(FakeEmbedder(), tienda.documentos)
