import discord, json, sqlite3
from discord.ext import commands
from typing import Literal, Optional
from discord.ext.commands import Greedy
from config import *
import traceback

class Owner(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(hidden=True)
    @commands.is_owner()
    async def reload(self, ctx, extension):
        await self.client.reload_extension(f"cogs.{extension}")
        embed = discord.Embed(title='Reload', description=f'{extension} successfully reloaded', color=0xff00c8)
        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def server_info(self, ctx):
        try:
            embed = discord.Embed(title='servers')
            for guild in self.client.guilds:
                embed.add_field(name=f'{guild.name}', value=f'Members count: {len(guild.members)}', inline=False)
            await ctx.send(embed=embed)
        except Exception as errors:
            print(f"Bot Error: {errors}")

    @commands.command(hidden=True)
    @commands.guild_only()
    @commands.is_owner()
    async def emulatejoin(self, ctx):
        test_guild = self.client.get_guild(ctx.guild.id)
        await self.client.on_guild_join(test_guild)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def eval(self, ctx, code):
        try:
            result = eval(code)
            if result is not None:
                await ctx.send(result)
        except:
            await ctx.send(f"An error occurred\n{traceback.format_exc()}")

async def setup(client):
    await client.add_cog(Owner(client))