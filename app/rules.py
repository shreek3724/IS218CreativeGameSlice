"""Pure restoration-game domain rules."""

from dataclasses import dataclass, field

GRID_SIZE = 4
SURFACE_DIRT = 2
OVERPAINT = 1
AGED_VARNISH = 0
LOW_RISK_CELLS = frozenset({(1, 1), (1, 2), (2, 1), (2, 2)})
BORDER_CELLS = frozenset(
    (row, column)
    for row in range(GRID_SIZE)
    for column in range(GRID_SIZE)
    if row in {0, GRID_SIZE - 1} or column in {0, GRID_SIZE - 1}
)
INTEGRITY_PENALTY = 10.0


@dataclass(frozen=True)
class CellState:
    """One grid cell and the layers already removed from it."""

    row: int
    column: int
    cleared_layers: frozenset[int] = field(default_factory=frozenset)

    def clear(self, layer: int) -> "CellState":
        """Return this cell with one additional cleared layer."""
        return CellState(self.row, self.column, self.cleared_layers | {layer})


@dataclass(frozen=True)
class MoveEvaluation:
    """The non-mutating result of checking one restoration move."""

    valid: bool
    reason: str


def _matches_clue(chemicals: dict[str, int], tool: str, expected, expected_tool: str):
    return tool == expected_tool and all(
        chemicals.get(name) == amount for name, amount in expected.items()
    )


def _evaluate_layer(
    grid, coordinate, chemicals, tool, layer, zone, ratio, expected_tool
):
    if coordinate not in zone:
        return MoveEvaluation(False, "unsafe zone")
    if grid.layer_complete(layer):
        return MoveEvaluation(False, "layer already cleared")
    if layer == OVERPAINT and not grid.layer_complete(SURFACE_DIRT):
        return MoveEvaluation(False, "surface dirt must be cleared first")
    if layer == AGED_VARNISH and not grid.layer_complete(OVERPAINT):
        return MoveEvaluation(False, "overpaint must be cleared first")
    if layer in grid.cell(*coordinate).cleared_layers:
        return MoveEvaluation(False, "cell layer already cleared")
    if not _matches_clue(chemicals, tool, ratio, expected_tool):
        return MoveEvaluation(False, "incorrect solvent or tool")
    return MoveEvaluation(True, "valid move")


def surface_dirt_strategy(grid, coordinate, chemicals, tool):
    """Evaluate Surface Dirt removal through the strategy interface."""
    return _evaluate_layer(
        grid,
        coordinate,
        chemicals,
        tool,
        SURFACE_DIRT,
        LOW_RISK_CELLS,
        {"water_ratio": 70, "oil_ratio": 30, "acid_ratio": 0},
        "swab",
    )


def overpaint_strategy(grid, coordinate, chemicals, tool):
    """Evaluate Overpaint removal through the strategy interface."""
    return _evaluate_layer(
        grid,
        coordinate,
        chemicals,
        tool,
        OVERPAINT,
        LOW_RISK_CELLS,
        {"water_ratio": 20, "oil_ratio": 70, "acid_ratio": 10},
        "brush",
    )


def aged_varnish_strategy(grid, coordinate, chemicals, tool):
    """Evaluate Aged Varnish removal through the strategy interface."""
    return _evaluate_layer(
        grid,
        coordinate,
        chemicals,
        tool,
        AGED_VARNISH,
        BORDER_CELLS,
        {"water_ratio": 10, "oil_ratio": 20, "acid_ratio": 70},
        "heat_lamp",
    )


LAYER_STRATEGIES = {
    SURFACE_DIRT: surface_dirt_strategy,
    OVERPAINT: overpaint_strategy,
    AGED_VARNISH: aged_varnish_strategy,
}


def evaluate_move_conditional(grid, layer, coordinate, chemicals, tool):
    """Evaluate a move using conditionals, for Strategy-pattern parity checks."""
    if layer == SURFACE_DIRT:
        return _evaluate_layer(
            grid,
            coordinate,
            chemicals,
            tool,
            layer,
            LOW_RISK_CELLS,
            {"water_ratio": 70, "oil_ratio": 30, "acid_ratio": 0},
            "swab",
        )
    if layer == OVERPAINT:
        return _evaluate_layer(
            grid,
            coordinate,
            chemicals,
            tool,
            layer,
            LOW_RISK_CELLS,
            {"water_ratio": 20, "oil_ratio": 70, "acid_ratio": 10},
            "brush",
        )
    if layer == AGED_VARNISH:
        return _evaluate_layer(
            grid,
            coordinate,
            chemicals,
            tool,
            layer,
            BORDER_CELLS,
            {"water_ratio": 10, "oil_ratio": 20, "acid_ratio": 70},
            "heat_lamp",
        )
    return MoveEvaluation(False, "unknown layer")


def calculate_score(integrity: float, clue_accuracy: float) -> float:
    """Return the server-calculated 60% integrity / 40% clue score."""
    return round((integrity * 0.60) + (clue_accuracy * 0.40), 2)


class PaintingGrid:
    """Own the 4x4 restoration state and apply checked moves."""

    def __init__(self):
        self._cells = {
            (row, column): CellState(row, column)
            for row in range(GRID_SIZE)
            for column in range(GRID_SIZE)
        }
        self.integrity = 100.0
        self._attempts = 0
        self._correct_moves = 0

    def cell(self, row: int, column: int) -> CellState:
        """Return a grid cell, rejecting coordinates outside the 4x4 board."""
        try:
            return self._cells[(row, column)]
        except KeyError as error:
            raise ValueError("coordinate is outside the grid") from error

    def layer_complete(self, layer: int) -> bool:
        """True when every cell targeted by a layer has been cleared."""
        zone = BORDER_CELLS if layer == AGED_VARNISH else LOW_RISK_CELLS
        return all(
            layer in self.cell(*coordinate).cleared_layers for coordinate in zone
        )

    @property
    def cell_states(self) -> tuple[CellState, ...]:
        """Return immutable cell state for a presentation adapter."""
        return tuple(self._cells.values())

    @property
    def clue_accuracy(self) -> float:
        """Return correct clue choices as a percentage."""
        if not self._attempts:
            return 0.0
        return round((self._correct_moves / self._attempts) * 100, 2)

    @property
    def final_score(self) -> float:
        """Return the current server-calculated score."""
        return calculate_score(self.integrity, self.clue_accuracy)

    def apply_move(self, layer: int, coordinate, chemicals: dict[str, int], tool: str):
        """Apply a Strategy-checked move and return its evaluation."""
        evaluator = LAYER_STRATEGIES.get(layer)
        result = (
            evaluator(self, coordinate, chemicals, tool)
            if evaluator
            else MoveEvaluation(False, "unknown layer")
        )
        self._attempts += 1
        if result.valid:
            self._correct_moves += 1
            self._cells[coordinate] = self.cell(*coordinate).clear(layer)
        else:
            self.integrity = max(0.0, self.integrity - INTEGRITY_PENALTY)
        return result
