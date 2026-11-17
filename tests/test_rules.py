"""Focused tests for pure restoration rules."""

import pytest

from app.rules import (
    AGED_VARNISH,
    BORDER_CELLS,
    LAYER_STRATEGIES,
    LOW_RISK_CELLS,
    OVERPAINT,
    SURFACE_DIRT,
    PaintingGrid,
    calculate_score,
    evaluate_move_conditional,
)


MOVES = {
    SURFACE_DIRT: ({"water_ratio": 70, "oil_ratio": 30, "acid_ratio": 0}, "swab"),
    OVERPAINT: ({"water_ratio": 20, "oil_ratio": 70, "acid_ratio": 10}, "brush"),
    AGED_VARNISH: ({"water_ratio": 10, "oil_ratio": 20, "acid_ratio": 70}, "heat_lamp"),
}


def clear_layer(grid, layer):
    chemicals, tool = MOVES[layer]
    zone = BORDER_CELLS if layer == AGED_VARNISH else LOW_RISK_CELLS
    for coordinate in zone:
        assert grid.apply_move(layer, coordinate, chemicals, tool).valid


@pytest.mark.parametrize("layer", [SURFACE_DIRT, OVERPAINT, AGED_VARNISH])
def test_strategies_match_conditional_evaluation(layer):
    grid = PaintingGrid()
    chemicals, tool = MOVES[layer]
    strategy = LAYER_STRATEGIES[layer](grid, (1, 1), chemicals, tool)
    conditional = evaluate_move_conditional(grid, layer, (1, 1), chemicals, tool)
    assert strategy == conditional


def test_target_zones_control_layer_completion_and_order():
    grid = PaintingGrid()
    chemicals, tool = MOVES[SURFACE_DIRT]
    assert not grid.apply_move(SURFACE_DIRT, (0, 0), chemicals, tool).valid
    assert not grid.layer_complete(SURFACE_DIRT)
    clear_layer(grid, SURFACE_DIRT)
    assert grid.layer_complete(SURFACE_DIRT)
    clear_layer(grid, OVERPAINT)
    assert grid.layer_complete(OVERPAINT)
    clear_layer(grid, AGED_VARNISH)
    assert grid.layer_complete(AGED_VARNISH)


def test_invalid_solvent_tool_and_order_lower_integrity():
    grid = PaintingGrid()
    assert not grid.apply_move(OVERPAINT, (1, 1), *MOVES[OVERPAINT]).valid
    assert not grid.apply_move(
        SURFACE_DIRT, (1, 1), MOVES[SURFACE_DIRT][0], "brush"
    ).valid
    assert grid.integrity == 80.0
    assert grid.clue_accuracy == 0.0


def test_score_uses_server_side_sixty_forty_weighting():
    assert calculate_score(80, 50) == 68.0
