"""1.7.6, issue 42: el subtítulo del juego se traduce («Puerto Bravo» es el nombre de la ciudad y se queda), y la ficha de
Marisma Negra, que llega como componente, sale en el idioma del juego (la 1.7.5 lo arregla con los componentes de idioma)."""
import json
import os

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TITULO = {"en": "Puerto Bravo: Law of the Asphalt", "pt": "Puerto Bravo: Lei do Asfalto", "vi": "Puerto Bravo: Luật Nhựa Đường", "ru": "Пуэрто-Браво: Закон асфальта"}


@pytest.mark.parametrize("cod", sorted(TITULO))
def test_el_titulo_va_traducido_en_todos_sus_textos(cod):
    cat = json.load(open(os.path.join(RAIZ, "data", "idiomas", cod, "textos.json"), encoding="utf-8"))["textos"]
    assert cat["Puerto Bravo: Ley del Asfalto"] == TITULO[cod]
    assert not [k for k, v in cat.items() if "Ley del Asfalto" in k and "Ley del Asfalto" in v]


@pytest.mark.parametrize("cod", sorted(TITULO))
def test_la_ficha_de_marisma_negra_esta_traducida_en_cada_idioma(cod):
    info = json.load(open(os.path.join(RAIZ, "componentes_extra", "mod_marisma_negra", "marisma_negra.json"), encoding="utf-8"))["info"]
    mod = json.load(open(os.path.join(RAIZ, "traduccion", cod, "mods", "marisma_negra.json"), encoding="utf-8"))["textos"]
    assert mod.get(info["descripcion"]) and mod[info["descripcion"]] != info["descripcion"]
