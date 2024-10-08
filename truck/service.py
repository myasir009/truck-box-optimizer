"""Define the main controller as FastAPI app."""

from fastapi import FastAPI, HTTPException
from .model import BoxId, Coords, ProblemDto, PositionedBoxDto, PackingDto, Box, Dimensions, InfeasibleError
from .solver import pack_truck as pack_truck_solver
from tests.examples import iter_examples

app = FastAPI()

routes: dict[str, ProblemDto] = { name: problem for (name, problem, _) in iter_examples() }

@app.get("/routes")
def get_routes() -> dict[str, ProblemDto]:
    return routes

@app.get("/routes/{routeName}")
def get_route(routeName: str) -> ProblemDto:
    return routes[routeName]

@app.post("/boxes/{boxId}/size")
def set_box_size(box_id: BoxId, size: Coords) -> int:
    """Update the size of a box in all routes

    Returns the number of boxes updated.
    """
    count = 0
    for route in routes.values():
        for box in route.boxes:
            if box.box_id == box_id:
                box.size = Dimensions(*size)
                count += 1

    if not count:
        raise HTTPException(400)
    return count

@app.post("/truck:pack")
async def pack_truck(problem: ProblemDto) -> PackingDto:
    truck_model = Dimensions(*problem.truck)
    boxes_model = [Box(
        box_id=box.box_id,
        size=Dimensions(*box.size),
        route_order=box.route_order,
    ) for box in problem.boxes]

    try:
        packing = pack_truck_solver(truck_model, boxes_model)
    except InfeasibleError:
        raise HTTPException(500)
    except ValueError:
        raise HTTPException(400)

    return PackingDto(
        boxes=[
            PositionedBoxDto(
                box_id=box.box_id,
                size=box.size,
                offset=packing.box_offsets[box.box_id],
            )
            for box in boxes_model
        ]
    )
