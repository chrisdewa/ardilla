# basic example

from ardilla import Model, Engine, Field



class Pet(Model):
    id: int = Field(pk=True, auto=True)
    name: str
    love: int = 0


with Engine("foo.db") as engine:
    crud = engine.crud(Pet)

    # create a new pets
    for pet_name in {"fluffy", "fido", "snowball"}:
        crud.insert(name=pet_name)

    # read your pets
    fido = crud.get_or_none(name="fido")
    fluffy = crud.get_or_none(name="fluffy")
    snowball = crud.get_or_none(name="snowball")
    print(fido, fluffy, snowball, sep="\n")
    # update your pets
    fluffy.love += 10
    crud.save_one(fluffy)
    print(fluffy)
    # delete your pet
    crud.delete_many(fido, snowball)

    # check if everything works:
    pets = crud.get_all()
    assert len(pets) == 1, "Something went wrong!!"
    print("All done!")
