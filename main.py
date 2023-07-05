import asyncio
import discord
import json, os
from discord.ext import commands
from config import *
from discord.ext.commands import Greedy
from typing import Literal, Optional
from utils.utilites import _GetText as _

intents = discord.Intents.default()

class Client(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='!',
            intents = intents,
            application_id = BotSettings.application_id
        )

    async def on_ready(self):
        await client.change_presence(activity=discord.Game(name=BotSettings.status))
        client.tree.copy_global_to(guild=discord.Object(id=BotSettings.support_server))

        print('Client ready.')

        # if BotSettings.status_roll_active:
        #     while True:
        #         for status in StatusRoll.Statuses:

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"{Emojis.Events.error} {_('error-command-on-cooldown', ctx.guild.id).format(round(error.retry_after, 2))}")
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send(f"{Emojis.Events.error} {_('error-user-not-found', ctx.guild.id)}")
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(f"{Emojis.Events.error} {_('error-bot-no-perms', ctx.guild.id)}")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send(f"{Emojis.Events.error} {_('error-no-permission', ctx.guild.id)}")
        elif isinstance(error, discord.ext.commands.errors.CommandNotFound):
            await ctx.send(f"{Emojis.Events.error} {_('error-command-not-found', ctx.guild.id)}")
        else:
            await ctx.send(f"{Emojis.Events.error} {_('error-unknown', ctx.guild.id).format(error)}")

    async def on_guild_join(self, guild):
        with open(Folders.settings, 'r', encoding='UTF-8') as f:
            towrite = json.load(f)
        if str(guild.preferred_locale).upper() == 'RU':
            language = 'RU'
        else:
            language = 'EN'
        towrite[str(guild.id)] = f'channel_nsfw/channel/{language}' # 1: channel_nsfw, 2: channel, 3: language
        with open(Folders.settings, 'w') as f:
            json.dump(towrite, f)
        embed = discord.Embed()

        async def sendwelcome(channel):
            await channel.send(embed=embed)
            return True

        for channel in guild.text_channels:
            try:
                if await sendwelcome(channel) is True: break
            except:
                pass
        print('NEW GUILD', f'ID: {guild.id}, NAME: {guild}, LANGUAGE: {language}')

    async def setup_hook(self):
        print(f"\033[31mLogged in as {client.user}\033[39m")
        cogs_folder = f"{os.path.abspath(os.path.dirname(__file__))}/cogs"
        for filename in os.listdir(cogs_folder):
            if filename.endswith(".py"):
                await client.load_extension(f"cogs.{filename[:-3]}")
        await client.tree.sync()

client = commands.Bot(command_prefix='!', intents=intents)
bot = commands.Bot(command_prefix='!', intents=intents)

client = Client()


client.run(BotSettings.token)