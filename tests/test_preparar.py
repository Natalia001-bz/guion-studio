from guion_studio.config import POR_DEFECTO
from guion_studio.preparar import calcular_tramos

P = POR_DEFECTO["preparar"]


def test_corta_silencio_inicial_y_final_con_margen():
    # silencio 0-1,2 s y desde 9 s hasta el final (10 s)
    tramos = calcular_tramos(10.0, [(0.0, 1.2), (9.0, 10.0)], P)
    assert tramos == [(0.95, 9.4)]


def test_acorta_pausas_largas_y_respeta_las_cortas():
    # pausa larga (3-5 s) y pausa corta (6-6,5 s)
    tramos = calcular_tramos(10.0, [(3.0, 5.0), (6.0, 6.5)], P)
    assert tramos == [(0.0, 3.175), (4.825, 10.0)]
    conservado = sum(b - a for a, b in tramos)
    assert abs(conservado - (10 - 2 + 0.35)) < 0.01


def test_une_silencios_separados_por_un_clic():
    # dos silencios finales separados por 0,1 s (un clic al detener la grabación)
    tramos = calcular_tramos(10.0, [(7.0, 8.0), (8.1, 10.0)], P)
    assert tramos == [(0.0, 7.4)]


def test_sin_silencios_conserva_todo():
    assert calcular_tramos(5.0, [], P) == [(0.0, 5.0)]
