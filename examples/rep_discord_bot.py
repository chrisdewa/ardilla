from ardilla import Model, Field, ForeignField
from ardilla.asyncio import Engine

from discord import Intents, Member
from discord.ext.commands import Bot, Context, guild_only

# db engine
engine = Engine("discobot.sqlite3", enable_foreing_keys=True)


# models
class GuildTable(Model):
    __tablename__ = "guilds"
    id: int = Field(primary=True)


class MembersTable(Model):
    __tablename__ = "members"
    id: int
    guild_id: int = ForeignField(
        references=GuildTable,
        on_delete=ForeignField.CASCADE
    )
    reputation: int = 0


# bot stuff
TOKEN = "GENERATE YOUR TOKEN FROM DISCORD'S DEVELOPERS' PORTAL"
intents = Intents.default()
intents.members = True
intents.message_content = True

class RepBot(Bot):
    def __init__(self):
        super().__init__(command_prefix='!', intents=intents)
    
    async def setup_hook(self):
        # connect the engine
        await engine.connect()
        # setup the table's cache
        self.gcrud = await engine.crud(GuildTable)
        self.mcrud = await engine.crud(MembersTable)
    
    async def close(self):
        # close engine
        await engine.close()
        return await super().close()

bot = RepBot()


@bot.command()
@guild_only()
async def thank(ctx: Context, member: Member):
    if member == ctx.author:
        return await ctx.send("You can't thank yourself")
    
    await bot.gcrud.insert_or_ignore(id=ctx.guild.id)
    dbmember, _ = await bot.mcrud.get_or_create(id=member.id, guild_id=ctx.guild.id)
    dbmember.reputation += 1
    await bot.mcrud.save_one(dbmember)
    await ctx.send(
        f"{member.mention} was thanked. Their reputation is now {dbmember.reputation}"
    )


@bot.command()
@guild_only()
async def reputation(ctx: Context, member: Member | None = None):
    member = member or ctx.author
    await bot.gcrud.insert_or_ignore(id=ctx.guild.id)
    dbmember, _ = await bot.mcrud.get_or_create(id=member.id, guild_id=ctx.guild.id)
    await ctx.send(f"{member.mention} has a reputation of {dbmember.reputation}")


bot.run(TOKEN)
