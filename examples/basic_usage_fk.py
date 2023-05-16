# basic example

from ardilla import Model, Engine, Field

engine = Engine("foo.db", enable_foreing_keys=True)

class Owner(Model):
    id: int = Field(pk=True, auto=True)
    name: str


class Pet(Model):
    __schema__ = '''
    CREATE TABLE IF NOT EXISTS pet(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        owner_id INTEGER,
        FOREIGN KEY (owner_id)
            REFERENCES owner(id)
            ON DELETE CASCADE
    );
    '''
    id: int = Field(pk=True, auto=True)
    name: str
    owner_id: int
    
# create crud helpers
owcrud = engine.crud(Owner)
petcrud = engine.crud(Pet)

# create owners
chris = owcrud.insert(name='chris')
liz = owcrud.insert(name='liz')

# Create objects with relationships
melly = petcrud.insert(name='melly', owner_id=liz.id)
wolke = petcrud.insert(name='wolke', owner_id=chris.id)
shirley = petcrud.insert(name='shirley', owner_id=chris.id)

# delete owner and test CASCADING EFFECT
owcrud.delete_one(chris)

pets = petcrud.get_all()
owners = owcrud.get_all()
print(pets)
print(owners)
assert len(pets) == 1, "Foreign keys didn't cascade"
print('All done, foreign key constrains work')
