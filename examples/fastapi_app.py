from typing import Annotated

from fastapi import FastAPI, Depends, status, HTTPException
from pydantic import BaseModel

from ardilla import Model
from ardilla.asyncio import Engine, Crud
from ardilla.errors import QueryExecutionError

app = FastAPI(docs_url="/")  # set the docs to index for easier access


class Item(Model):
    id: int  # this sets the id as primary key in the default schema
    name: str
    price: float


class PatchedItem(BaseModel):
    name: str
    price: float


engine = Engine("fastapi_app.sqlite3")
Crud.engine = engine  # this sets the engine for all crud instances
crud: Crud[Item] = Crud(Item)  # the typehint enables ide autocomplete


@app.on_event("startup")
async def on_startup_event():
    await engine.setup()  # executes the table schemas


async def get_item_by_id(id_: int) -> Item | int:
    """Returns the item with the specified id
    If there's not such item in the database, the original id is returned instead

    """
    item = await crud.get_or_none(id=id_)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No item with {id_} was found in the database",
        )
    return item


item_by_id_deps = Annotated[Item, Depends(get_item_by_id)]


@app.post("/items/new")
async def create_item(item: Item) -> Item:
    try:
        await crud.insert(**item.dict())
    except QueryExecutionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Item with {item.id} was already found in the database",
        )
    return item


@app.get("/items/{id}")
async def get_item_route(item: item_by_id_deps) -> Item:
    return item


@app.get("/items")
async def get_all_items():
    return await crud.get_all()


@app.patch("/items/{id}")
async def patch_item(item: item_by_id_deps, patched: PatchedItem):
    item.name = patched.name
    item.price = patched.price
    await crud.save_one(item)
    return item


@app.delete("/item/{id}")
async def delete_item(item: item_by_id_deps):
    await crud.delete_one(item)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)
