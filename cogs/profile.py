import asyncio
import discord, json, sqlite3, requests
from discord.ext import commands
from PIL import Image
from io import BytesIO
from typing import Literal, Optional
from discord.ext.commands import Greedy
from config import *
from discord import app_commands
from utils.utilites import _GetText as _
from utils.utilites import *

class Profile(commands.Cog):
    '''Interact with Danbooru bot Profiles.'''
    def __init__(self, client):
        self.client = client

    @commands.hybrid_command(name='favorites')
    @app_commands.describe(
        member='Choose member or leave blank to view your favorites',
    )
    @commands.cooldown(1, 7, commands.BucketType.user)
    async def Favorite(self, ctx, member: discord.Member = None):
        '''View member favorite list'''
        if CheckServer(ctx.guild, ctx.author) is False:
            class SelectMenu(discord.ui.Select):
                def __init__(self):
                    options = [(discord.SelectOption(label='English',
                                                 description='Use english language.')),
                               (discord.SelectOption(label='Русский',
                                                 description='Использовать русский язык.')),]

                    super().__init__(placeholder='Language', min_values=1, max_values=1,
                                     options=options)

                async def callback(self, interaction: discord.Interaction):
                    if str(self.values[0]) == 'English':
                        ChangeLang(ctx.author, 'EN')
                        await interaction.response.send_message(_('changed-lang-to-EN', ctx.author.id), ephemeral=True)
                    elif str(self.values[0]) == 'Русский':
                        ChangeLang(ctx.author, 'RU')
                        await interaction.response.send_message(_('changed-lang-to-RU', ctx.author.id), ephemeral=True)

            view = discord.ui.View()
            view.add_item(item=SelectMenu())
            return await ctx.send(embed=UserFirstTime(ctx.author), view=view, ephemeral=True)

        CheckUser(ctx.author.id)

        if member is None:
            member = ctx.author
        else:
            if isPrivate(member.id):
                return await ctx.send(_('member-private', ctx.author.id).format(member.name), ephemeral=True)

        def getlist(member):
            with open(Folders.favorites, 'r', encoding='UTF-8') as f:
                data = json.load(f)
                user = data[str(member.id)]
                return str(user).split(';')

        listids = getlist(member)

        headers = {
            'User-Agent': 'Mozilla/5.0',
        }

        message = await ctx.send(embed=discord.Embed(description=_('loading', ctx.author.id), title=''), ephemeral=True)

        if len(str(len(listids))) < 2:
            pages = 1
        else:
            pages = int(list(str(len(listids)))[0]) + 1

        async def drawmessage(id):
            def getpost(id):
                request = requests.get(f'https://danbooru.donmai.us/posts/{str(id)}.json', headers=headers).json()
                return request

            async def rightbutton(interaction: discord.Interaction):
                await interaction.response.send_message(
                    _('transition-to', ctx.author.id).format(f'{index + 2}/{len(listids)}'), ephemeral=True)
                await drawmessage(listids[index + 1])

            async def leftbutton(interaction: discord.Interaction):
                await interaction.response.send_message(
                    _('transition-to', ctx.author.id).format(f'{index}/{len(listids)}'), ephemeral=True)
                await drawmessage(listids[index - 1])

            async def unfavorite(interaction: discord.Interaction):
                await interaction.response.send_message()
                removeFromFavorite(member.id, listids[index])


            post = getpost(id)
            index = listids.index(str(id))

            button_left = discord.ui.Button(label=_('left', ctx.author.id), style=discord.ButtonStyle.grey)
            button_right = discord.ui.Button(label=_('right', ctx.author.id), style=discord.ButtonStyle.grey)

            button_right.callback = rightbutton
            button_left.callback = leftbutton

            if index == 0:
                button_left.disabled = True
            if index == len(listids) - 1:
                button_right.disabled = True

            view = discord.ui.View()
            view.add_item(item=button_left)
            if member == ctx.author:
                button_unfavorite = discord.ui.Button(label=_('unfavorite', ctx.author.id),
                                                      style=discord.ButtonStyle.red)
                button_unfavorite.callback = unfavorite
                view.add_item(item=button_unfavorite)
            view.add_item(item=button_right)

            selectmenu = SelectMenu(ctx.author.id)

            try:
                link = discord.ui.Button(label=_('original', ctx.author.id), style=discord.ButtonStyle.link,
                                         emoji=Emojis.Buttons.link, url=post['large_file_url'], row=2)
            except KeyError:
                link = discord.ui.Button(label=_('original', ctx.author.id), style=discord.ButtonStyle.link,
                                         emoji=Emojis.Buttons.link, url=post['file_url'], row=2)

            view.add_item(item=link)
            Disabledview.add_item(item=link)

            try:
                if post['source'].startswith('https://'):
                    src = discord.ui.Button(label=_('art-source', ctx.author.id), style=discord.ButtonStyle.link,
                                            emoji=Emojis.Buttons.link, url=post['source'], row=2)
                    view.add_item(item=src)
                    Disabledview.add_item(item=src)
            except: True

            view.add_item(item=selectmenu)

            response = requests.get(post['file_url'])
            img = Image.open(BytesIO(response.content))
            pixels = img.convert('RGB').getcolors(img.size[0] * img.size[1])
            most_common_color = max(pixels, key=lambda x: x[0])[1]
            col = (str(most_common_color).replace("(", "").replace(")", "").split(','))

            embed = discord.Embed(title='', description='',
                                  color=discord.Color.from_rgb(int(col[0]), int(col[1]), int(col[2])))
            embed.set_image(url=post['file_url'])

            embed.set_author(name=f'{member.name} ({index+1}/{len(listids)})', icon_url=member.avatar.url)

            try:
                if post["tag_string_artist"] != '': artist = _('art-artist', ctx.author.id).format(post["tag_string_artist"])
                else: artist = ''
            except: artist = ''
            try:
                if post["tag_string_copyright"] != '': copyright = _('art-copyright', ctx.author.id).format(post["tag_string_copyright"])
                else: copyright = ''
            except: copyright = ''
            try:
                if post['tag_string_character'] != '': character = _('art-characters', ctx.author.id).format(post['tag_string_character'])
                else: character = ''
            except: character = ''
            try:
                if post['source'].startswith('https://'): source = f"[{_('art-source', ctx.author.id)}]({post['source']})"
                else: source = ''
            except: source = ''

            embed.add_field(name='', value=f'''
                                ID: **{post["id"]}**
                                {_('art-rating', ctx.author.id).format(post["rating"].upper())}
                                {artist}
                                {character}
                                {copyright}
                                ''')

            await message.edit(embed=embed, view=view)

        class SelectMenu(discord.ui.Select):
            def __init__(self, guild_id):
                self.guild_id = guild_id
                options = []
                for x in range(int(pages)):
                    if int(pages) >= 2:
                        ids = listids[x * 10:(x + 1) * 10]
                    else:
                        ids = listids
                    options.append(
                        discord.SelectOption(label=_("page", guild_id).format(x + 1), description=f'{", ".join(ids)}'))

                super().__init__(placeholder=_('placeholder-select-page', guild_id), min_values=1, max_values=1,
                                 options=options)

            async def callback(self, interaction: discord.Interaction):
                for option in self.options:
                    if str(option.label) == str(self.values[0]):
                        await interaction.response.send_message(
                            _('transition-to', ctx.author.id).format(option.label.lower()), ephemeral=True)
                        await drawmessage(str(option.description).split(', ')[0])

        Disabledview = discord.ui.View()
        button_left = discord.ui.Button(label=_('left', ctx.author.id), style=discord.ButtonStyle.grey)
        button_right = discord.ui.Button(label=_('right', ctx.author.id), style=discord.ButtonStyle.grey)
        button_left.disabled = True
        Disabledview.add_item(item=button_left)
        if ctx.author.id == member.id:
            button_unfavorite = discord.ui.Button(label=_('unfavorite', ctx.author.id),
                                                  style=discord.ButtonStyle.red)
            button_unfavorite.disabled = True
            Disabledview.add_item(item=button_unfavorite)
        button_right.disabled = True
        Disabledview.add_item(item=button_right)

        await drawmessage(listids[0])
        await asyncio.sleep(60*3)
        return await message.edit(view=Disabledview)

    @commands.hybrid_command(name='profive-settings')
    @app_commands.describe(
        private='Make your profile private / public',
        language='Choose bot language'
    )
    @app_commands.choices(private=[
        app_commands.Choice(name="Private", value="private"),
        app_commands.Choice(name="Public", value="public"),
    ])
    @app_commands.choices(language=[
        app_commands.Choice(name="English", value="EN"),
        app_commands.Choice(name="Русский", value="RU"),
    ])
    @commands.cooldown(1, 7, commands.BucketType.user)
    async def ProfileSettings(self, ctx, language: app_commands.Choice[str] = None, private: app_commands.Choice[str] = None):
        '''Redact your Danbooru bot Profile.'''
        if CheckServer(ctx.guild, ctx.author) is False:
            class SelectMenu(discord.ui.Select):
                def __init__(self):
                    options = [(discord.SelectOption(label='English',
                                                 description='Use english language.')),
                               (discord.SelectOption(label='Русский',
                                                 description='Использовать русский язык.')),]

                    super().__init__(placeholder='Language', min_values=1, max_values=1,
                                     options=options)

                async def callback(self, interaction: discord.Interaction):
                    if str(self.values[0]) == 'English':
                        ChangeLang(ctx.author, 'EN')
                        await interaction.response.send_message(_('changed-lang-to-EN', ctx.author.id), ephemeral=True)
                    elif str(self.values[0]) == 'Русский':
                        ChangeLang(ctx.author, 'RU')
                        await interaction.response.send_message(_('changed-lang-to-RU', ctx.author.id), ephemeral=True)

            view = discord.ui.View()
            view.add_item(item=SelectMenu())
            return await ctx.send(embed=UserFirstTime(ctx.author), view=view, ephemeral=True)

        CheckUser(ctx.author.id)

        if language is not None:
            ChangeLang(ctx.author, language.value)
            await ctx.send(_(f'changed-lang-to-{language.value}', ctx.author.id), ephemeral=True)

        if private is not None:
            await ctx.send(_(changePrivate(ctx.author.id, private.value), ctx.author.id), ephemeral=True)

async def setup(client):
    await client.add_cog(Profile(client))