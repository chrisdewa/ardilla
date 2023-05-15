from ardilla import Model, Field
from ardilla.asyncio import Engine

from discord import Intents, Member
from discord.ext.commands import Bot, Context, guild_only

# db engine
engine = Engine("discobot.sqlite3")


# models
class GuildTable(Model):
    __tablename__ = "guilds"
    id: int = Field(primary=True)


class MembersTable(Model):
    __tablename__ = "members"
    __schema__ = """
    CREATE TABLE IF NOT EXISTS members(
        id INTEGER PRIMARY KEY,
        guild_id INTEGER,
        reputation INTEGER DEFAULT 0,
        FOREIGN KEY (guild_id) 
            REFERENCES guilds(id)
            ON DELETE CASCADE
    );
    """
    id: int
    guild_id: int
    reputation: int = Field(default=0)


# cruds
# first because of the relationship in members
guild_crud = engine.crud(GuildTable)
member_crud = engine.crud(MembersTable)

with engine as connection:
    # use the engine as a context manager
    # for specific queries
    connection.execute("PRAGMA foreign_keys = ON;")
    connection.commit()


# bot stuff
TOKEN = "GENERATE YOUR TOKEN FROM DISCORD'S DEVELOPERS' PORTAL"
intents = Intents.default()
intents.members = True
intents.message_content = True

bot = Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Bot is ready")


@bot.command()
@guild_only()
async def thank(ctx: Context, member: Member):
    if member == ctx.author:
        return await ctx.send("You can't thank yourself")
    await guild_crud.insert_or_ignore(id=ctx.guild.id)
    dbmember, _ = await member_crud.get_or_create(id=member.id, guild_id=ctx.guild.id)
    dbmember.reputation += 1
    await member_crud.save_one(dbmember)
    await ctx.send(
        f"{member.mention} was thanked. Their reputation is now {dbmember.reputation}"
    )


@bot.command()
@guild_only()
async def reputation(ctx: Context, member: Member | None = None):
    member = member or ctx.author
    await guild_crud.insert_or_ignore(id=ctx.guild.id)
    dbmember, _ = await member_crud.get_or_create(id=member.id, guild_id=ctx.guild.id)
    await ctx.send(f"{member.mention} has a reputation of {dbmember.reputation}")


bot.run(TOKEN)
