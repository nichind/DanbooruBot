import asyncio
import discord, json, sqlite3, random, requests, aiohttp, io
from discord.ext import commands
from discord import components, Button, File
from typing import Literal, Optional
from utils.utilites import *
from config import *
from PIL import Image
from io import BytesIO
from utils.utilites import _GetText as _
from discord import app_commands

class Danbooru(commands.Cog):
    '''Interact with Danbooru API.'''
    def __init__(self, client):
        self.client = client

    @commands.hybrid_command(name='feed')
    @app_commands.describe(
        tag = 'Search for specific tags in New Posts.',
        nsfw = 'Filter NSFW content.',
    )
    @app_commands.choices(nsfw=[
        app_commands.Choice(name="Don't show", value="0"),
        app_commands.Choice(name="Show", value="1"),
        app_commands.Choice(name="Only NSFW", value="2"),
    ])
    @commands.cooldown(1, 7, commands.BucketType.user)
    async def Feed(self, ctx, tag: str = '', nsfw: app_commands.Choice[str]=None):
        '''Get last post on Danbooru. Tag is optional, Filter is optional.'''
        if CheckServer(ctx.guild, ctx.author) is False:
            class SelectMenu(discord.ui.Select):
                def __init__(self):
                    options = [(discord.SelectOption(label='English',
                                                     description='Use english language.')),
                               (discord.SelectOption(label='Русский',
                                                     description='Использовать русский язык.')), ]

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

        headers = {
            'User-Agent': 'Mozilla/5.0',
        }

        def GetLastPost(iteration = 0, tags = ''):
            if tags != '':
                listarts = requests.get(f'https://danbooru.donmai.us/posts.json?tags={tags}', headers=headers).json()
                request = requests.get(f'https://danbooru.donmai.us/posts/{listarts[iteration]["id"]}.json', headers=headers).json()
            else:
                request = requests.get(f'https://danbooru.donmai.us/posts/{str(int(count) - iteration)}.json', headers=headers).json()
            return (request, iteration)



        count = requests.get('https://danbooru.donmai.us/posts.json', headers=headers).json()[0]['id']

        nsfw_channel, sent, anslist = ctx.channel.nsfw, False, []

        value = '0'
        if nsfw is not None:
            filter = _('filter', ctx.author.id).format(nsfw.name)
            if nsfw_channel is False and nsfw.value in ['1', '2']:
                value = nsfw.value
                message = await ctx.send(embed=discord.Embed(description=_('loading', ctx.author.id), title=''), ephemeral = True)
                #return await ctx.send(_('channel-is-not-nsfw', ctx.guild.id), ephemeral = True)
            elif nsfw_channel is True and nsfw.value in ['1', '2']:
                value = nsfw.value
                message = await ctx.send(embed=discord.Embed(description=_('loading', ctx.author.id), title=''),
                                         ephemeral=False)
        else:
            filter = _('filter', ctx.author.id).format("Don't show")
            message = await ctx.send(embed=discord.Embed(description=_('loading', ctx.author.id), title=''),
                                     ephemeral=False)


        if tag is None:
            post, iteration = GetLastPost()
        else: post, iteration = GetLastPost(tags=tag)

        def getmessage(post, iteration):
            async def refresh_post(interaction: discord.Interaction):
                if interaction.user.id == ctx.author.id:
                    await interaction.response.send_message(
                        embed=discord.Embed(description=_('loading', ctx.author.id), title=''), ephemeral=True)
                    found = False
                    post, iteration = GetLastPost(iteration=1, tags=tag)
                    while found is False:
                        if post['rating'] in ['q', 'e'] and nsfw_channel is False and value in ['1', '2'] and post['id'] not in anslist:
                            anslist.append(post['id'])
                            embed, view, disabled_view = getmessage(post, iteration)
                            await ctx.send(embed=embed, view=view, ephemeral=True)
                            await asyncio.sleep(60 * 2)
                            await message.edit(view=disabled_view)
                            found = True
                        elif post['rating'] in ['g', 's'] and value in ['2']:
                            anslist.append(post['id'])
                            post, iteration = GetLastPost(iteration=iteration + 1, tags=tag)
                        elif post['rating'] in ['q', 'e'] and value in ['0']:
                            anslist.append(post['id'])
                            post, iteration = GetLastPost(iteration=iteration + 1, tags=tag)
                        elif post['id'] in anslist:
                            post, iteration = GetLastPost(iteration=iteration + 1, tags=tag)
                        else:
                            anslist.append(post['id'])
                            embed, view, disabled_view = getmessage(post, iteration)
                            msg = await ctx.send(embed=embed, view=view)
                            await asyncio.sleep(60*2)
                            await msg.edit(view=disabled_view)
                            found = True
                else:
                    await interaction.response.send_message(_('no-permission-button', ctx.author.id), ephemeral=True)

            async def add_to_favorites(interaction: discord.Interaction):
                await interaction.response.send_message(
                    _(addToFavorite(interaction.user.id, id), ctx.author.id).format(id=id,
                                                                                   favorites=HyperCommands.Favorites), ephemeral=True)

            while True:
                try:
                    id = post['id']
                    image_url = post['file_url']
                    break
                except KeyError:
                    if tag is None:
                        post, iteration = GetLastPost()
                    else:
                        post, iteration = GetLastPost(tags=tag)

            response = requests.get(image_url)
            img = Image.open(BytesIO(response.content))
            pixels = img.convert('RGB').getcolors(img.size[0] * img.size[1])
            most_common_color = max(pixels, key=lambda x: x[0])[1]

            col = (str(most_common_color).replace("(", "").replace(")", "").split(','))
            try:
                link = discord.ui.Button(label=_('original', ctx.author.id), style=discord.ButtonStyle.link,
                                         emoji=Emojis.Buttons.link, url=post['large_file_url'], row=2)
            except KeyError:
                link = discord.ui.Button(label=_('original', ctx.author.id), style=discord.ButtonStyle.link,
                                         emoji=Emojis.Buttons.link, url=post['file_url'])
            button = discord.ui.Button(label=_('refresh', ctx.author.id), style=discord.ButtonStyle.grey,
                                     emoji=Emojis.Buttons.refresh)
            favorite = discord.ui.Button(label=_('add-favorite', ctx.author.id), style=discord.ButtonStyle.red,
                                       emoji=Emojis.Buttons.favorites)
            favorite.callback = add_to_favorites
            button.callback = refresh_post
            view = discord.ui.View()

            view.add_item(item=button)
            view.add_item(item=favorite)
            view.add_item(item=link)
            try:
                if post['source'].startswith('https://'):
                    src = discord.ui.Button(label=_('art-source', ctx.author.id), style=discord.ButtonStyle.link,
                                            emoji=Emojis.Buttons.link, url=post['source'], row=2)
                    view.add_item(item=src)
            except: True


            button_disabled = discord.ui.Button(label=_('refresh', ctx.author.id), style=discord.ButtonStyle.grey,
                                       emoji=Emojis.Buttons.refresh, disabled=True)
            favorite_disabled = discord.ui.Button(label=_('add-favorite', ctx.author.id), style=discord.ButtonStyle.red,
                                         emoji=Emojis.Buttons.favorites, disabled=True)

            disabled_view = discord.ui.View()
            disabled_view.add_item(item=button_disabled)
            disabled_view.add_item(item=favorite_disabled)
            disabled_view.add_item(item=link)
            try:
                disabled_view.add_item(item=src)
            except: True

            embed = discord.Embed(title='', description='',
                                  color=discord.Color.from_rgb(int(col[0]), int(col[1]), int(col[2])))
            embed.set_image(url=image_url)
            embed.set_author(name=f'{ctx.author.name}', icon_url=ctx.author.avatar.url)
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
            {filter}
            ID: **{post["id"]}**
            {_('art-rating', ctx.author.id).format(post["rating"].upper())}
            {artist}
            {character}
            {copyright}
            ''')
            return (embed, view, disabled_view)

        while sent is False:
            # if post['rating'] in ['q', 'e'] and nsfw_channel is False or post['id'] in anslist:
            #     post, iteration = GetLastPost(iteration=iteration + 1)
            if post['rating'] in ['q', 'e'] and nsfw_channel is False and value in ['1', '2']:
                anslist.append(post['id'])
                embed, view, disabled_view = getmessage(post, iteration)
                await message.edit(embed=embed, view=view)
                await asyncio.sleep(60 * 2)
                await message.edit(view=disabled_view)
                sent = True
            elif post['rating'] in ['g', 's'] and value in ['2']:
                anslist.append(post['id'])
                post, iteration = GetLastPost(iteration=iteration + 1, tags=tag)
            elif post['rating'] in ['q', 'e'] and value in ['0']:
                anslist.append(post['id'])
                post, iteration = GetLastPost(iteration=iteration + 1, tags=tag)
            else:
                anslist.append(post['id'])
                embed, view, disabled_view = getmessage(post, iteration)
                await message.edit(embed=embed, view=view)
                await asyncio.sleep(60 * 2)
                await message.edit(view=disabled_view)
                sent = True

    @commands.hybrid_command(name='post')
    @app_commands.describe(
        id='Id of Post you want to search.',
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def GetPost(self, ctx, id: int):
        '''Get post by id on Danbooru.'''
        CheckServer(ctx.guild)
        CheckUser(ctx.author.id)

        headers = {
            'User-Agent': 'Mozilla/5.0',
        }

        nsfw_channel = ctx.channel.nsfw

        def GetPost(id):
            return (requests.get(f'https://danbooru.donmai.us/posts/{str(id)}.json',
                                 headers=headers).json())

        post = GetPost(id)
        try:
            if post['success'] is False:
                return await ctx.send(_('post-not-found', ctx.author.id).format(str(id)), ephemeral=True)
        except: True
        if post['rating'] in ['q', 'e'] and nsfw_channel is False:
            eph = True
            await ctx.send(embed=discord.Embed(description=_('since-channel-not-nsfw', ctx.author.id).format(rating=post['rating'].upper()), title=''), ephemeral=eph)
        else:
            eph = False

        message = await ctx.send(embed=discord.Embed(description=_('loading', ctx.author.id), title=''), ephemeral=eph)

        def getmessage(post):
            async def add_to_favorites(interaction: discord.Interaction):
                await interaction.response.send_message(
                    _(addToFavorite(interaction.user.id, id), ctx.author.id).format(id=id,
                                                                             favorites=HyperCommands.Favorites),
                    ephemeral=True)

            id = post['id']
            image_url = (post['file_url'])

            response = requests.get(image_url)
            img = Image.open(BytesIO(response.content))
            pixels = img.convert('RGB').getcolors(img.size[0] * img.size[1])
            most_common_color = max(pixels, key=lambda x: x[0])[1]

            col = (str(most_common_color).replace("(", "").replace(")", "").split(','))
            try:
                link = discord.ui.Button(label=_('original', ctx.author.id), style=discord.ButtonStyle.link,
                                         emoji=Emojis.Buttons.link, url=post['large_file_url'])
            except KeyError:
                link = discord.ui.Button(label=_('original', ctx.author.id), style=discord.ButtonStyle.link,
                                         emoji=Emojis.Buttons.link, url=post['file_url'])
            favorite = discord.ui.Button(label=_('add-favorite', ctx.author.id), style=discord.ButtonStyle.red,
                                         emoji=Emojis.Buttons.favorites)
            favorite.callback = add_to_favorites
            view = discord.ui.View()

            view.add_item(item=link)
            view.add_item(item=favorite)

            try:
                if post['source'].startswith('https://'):
                    src = discord.ui.Button(label=_('art-source', ctx.author.id), style=discord.ButtonStyle.link,
                                            emoji=Emojis.Buttons.link, url=post['source'], row=2)
                    view.add_item(item=src)
            except: True

            favorite_disabled = discord.ui.Button(label=_('add-favorite', ctx.author.id), style=discord.ButtonStyle.red,
                                                  emoji=Emojis.Buttons.favorites, disabled=True)

            disabled_view = discord.ui.View()
            disabled_view.add_item(item=link)
            disabled_view.add_item(item=favorite_disabled)
            try:
                disabled_view.add_item(item=src)
            except: True

            embed = discord.Embed(title='', description='',
                                  color=discord.Color.from_rgb(int(col[0]), int(col[1]), int(col[2])))
            embed.set_image(url=image_url)
            embed.set_author(name=f'{ctx.author.name}', icon_url=ctx.author.avatar.url)
            try:
                if post["tag_string_artist"] != '':
                    artist = _('art-artist', ctx.author.id).format(post["tag_string_artist"])
                else:
                    artist = ''
            except:
                artist = ''
            try:
                if post["tag_string_copyright"] != '':
                    copyright = _('art-copyright', ctx.author.id).format(post["tag_string_copyright"])
                else:
                    copyright = ''
            except:
                copyright = ''
            try:
                if post['tag_string_character'] != '':
                    character = _('art-characters', ctx.author.id).format(post['tag_string_character'])
                else:
                    character = ''
            except:
                character = ''
            try:
                if post['source'].startswith('https://'):
                    source = f"[{_('art-source', ctx.author.id)}]({post['source']})"
                else:
                    source = ''
            except:
                source = ''

            embed.add_field(name='', value=f'''
                    ID: **{post["id"]}**
                    {_('art-rating', ctx.author.id).format(post["rating"].upper())}
                    {artist}
                    {character}
                    {copyright}
                    ''')
            return (embed, view, disabled_view)


        embed, view, disabled_view = getmessage(post)
        await message.edit(embed=embed, view=view)
        await asyncio.sleep(60 * 2)
        return await message.edit(view=disabled_view)

    @commands.hybrid_command(name='random')
    @app_commands.describe(
        score='Minimum upvotes on post.',
        tag='Search for specific tags in New Posts.',
        nsfw='Filter NSFW content.',
    )
    @app_commands.choices(nsfw=[
        app_commands.Choice(name="Don't show", value="0"),
        app_commands.Choice(name="Show", value="1"),
        app_commands.Choice(name="Only NSFW", value="2"),
    ])
    @commands.cooldown(1, 7, commands.BucketType.user)
    async def Random(self, ctx, score: int = 25, tag: str = '', nsfw: app_commands.Choice[str] = None):
        '''Get random post on Danbooru. Tag is optional, Filter is optional.'''
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

        headers = {
            'User-Agent': 'Mozilla/5.0',
        }



        def GetRandomPost(iteration=0, tags='', score = 1):
            if tags != '':
                request = requests.get(f'https://danbooru.donmai.us/posts/random.json?tags={(f"score:>{score}+-status:deleted+{tags}")}', headers=headers).json()
            else:
                request = requests.get(f'https://danbooru.donmai.us/posts/random.json?tags={(f"score:>{score}+-status:deleted")}',
                                       headers=headers).json()
            return (request, iteration)

        count = requests.get('https://danbooru.donmai.us/posts.json', headers=headers).json()[0]['id']

        nsfw_channel, sent, anslist = ctx.channel.nsfw, False, []



        value = '0'
        if nsfw is not None:
            filter = _('filter', ctx.author.id).format(nsfw.name)
            if nsfw_channel is False and nsfw.value in ['1', '2']:
                value = nsfw.value
                message = await ctx.send(embed=discord.Embed(description=_('loading', ctx.author.id), title=''),
                                         ephemeral=True)
                # return await ctx.send(_('channel-is-not-nsfw', ctx.guild.id), ephemeral = True)
            elif nsfw_channel is True and nsfw.value in ['1', '2']:
                value = nsfw.value
                message = await ctx.send(embed=discord.Embed(description=_('loading', ctx.author.id), title=''),
                                         ephemeral=False)
            elif nsfw.value in ['0']:
                value = nsfw.value
                filter = _('filter', ctx.author.id).format("Don't show")
                message = await ctx.send(embed=discord.Embed(description=_('loading', ctx.author.id), title=''),
                                         ephemeral=False)
        else:
            value = '0'
            filter = _('filter', ctx.author.id).format("Don't show")
            message = await ctx.send(embed=discord.Embed(description=_('loading', ctx.author.id), title=''),
                                     ephemeral=False)

        if tag is None:
            post, iteration = GetRandomPost(score=score)
        else:
            post, iteration = GetRandomPost(tags=tag, score=score)

        if value in ['1', '2'] and nsfw_channel is False:
            eph = True
            await ctx.send(embed=discord.Embed(description=_('since-channel-not-nsfw-random', ctx.author.id).format(filter=filter), title=''), ephemeral=eph)
        else:
            eph = False

        def getmessage(post, iteration):
            async def refresh_post(interaction: discord.Interaction):
                if interaction.user.id == ctx.author.id:
                    await interaction.response.send_message(
                        embed=discord.Embed(description=_('loading', ctx.author.id), title=''), ephemeral=True)
                    found = False
                    post, iteration = GetRandomPost(iteration=1, tags=tag, score=score)
                    while found is False:
                        if post['rating'] in ['q', 'e'] and nsfw_channel is False and value in ['1', '2'] and post[
                            'id'] not in anslist:
                            anslist.append(post['id'])
                            embed, view, disabled_view = getmessage(post, iteration)
                            await ctx.send(embed=embed, view=view, ephemeral=True)
                            await asyncio.sleep(60 * 2)
                            await message.edit(view=disabled_view)
                            found = True
                        elif post['rating'] in ['g', 's'] and value in ['2']:
                            anslist.append(post['id'])
                            post, iteration = GetRandomPost(iteration=iteration + 1, tags=tag, score=score)
                        elif post['rating'] in ['q', 'e'] and value in ['0']:
                            anslist.append(post['id'])
                            post, iteration = GetRandomPost(iteration=iteration + 1, tags=tag, score=score)
                        elif post['id'] in anslist:
                            post, iteration = GetRandomPost(iteration=iteration + 1, tags=tag, score=score)
                        else:
                            anslist.append(post['id'])
                            embed, view, disabled_view = getmessage(post, iteration)
                            msg = await ctx.send(embed=embed, view=view)
                            await asyncio.sleep(60 * 2)
                            await msg.edit(view=disabled_view)
                            found = True
                else:
                    await interaction.response.send_message(_('no-permission-button', ctx.author.id), ephemeral=True)

            async def add_to_favorites(interaction: discord.Interaction):
                await interaction.response.send_message(
                    _(addToFavorite(interaction.user.id, id), ctx.author.id).format(id=id,
                                                                                   favorites=HyperCommands.Favorites),
                    ephemeral=True)

            while True:
                try:
                    id = post['id']
                    image_url = post['file_url']
                    break
                except KeyError:
                    if tag is None:
                        post, iteration = GetRandomPost(score=score)
                    else:
                        post, iteration = GetRandomPost(tags=tag, score=score)

            response = requests.get(image_url)
            img = Image.open(BytesIO(response.content))
            pixels = img.convert('RGB').getcolors(img.size[0] * img.size[1])
            most_common_color = max(pixels, key=lambda x: x[0])[1]

            col = (str(most_common_color).replace("(", "").replace(")", "").split(','))
            try:
                link = discord.ui.Button(label=_('original', ctx.author.id), style=discord.ButtonStyle.link,
                                         emoji=Emojis.Buttons.link, url=post['large_file_url'], row=2)
            except KeyError:
                link = discord.ui.Button(label=_('original', ctx.author.id), style=discord.ButtonStyle.link,
                                         emoji=Emojis.Buttons.link, url=post['file_url'], row=2)

            button = discord.ui.Button(label=_('refresh', ctx.author.id), style=discord.ButtonStyle.grey,
                                       emoji=Emojis.Buttons.refresh)
            favorite = discord.ui.Button(label=_('add-favorite', ctx.author.id), style=discord.ButtonStyle.red,
                                         emoji=Emojis.Buttons.favorites)
            favorite.callback = add_to_favorites
            button.callback = refresh_post
            view = discord.ui.View()

            view.add_item(item=button)
            view.add_item(item=link)

            view.add_item(item=favorite)

            button_disabled = discord.ui.Button(label=_('refresh', ctx.author.id), style=discord.ButtonStyle.grey,
                                                emoji=Emojis.Buttons.refresh, disabled=True)
            favorite_disabled = discord.ui.Button(label=_('add-favorite', ctx.author.id), style=discord.ButtonStyle.red,
                                                  emoji=Emojis.Buttons.favorites, disabled=True)

            disabled_view = discord.ui.View()
            disabled_view.add_item(item=button_disabled)
            disabled_view.add_item(item=link)
            disabled_view.add_item(item=favorite_disabled)

            try:
                if post['source'].startswith('https://'):
                    src = discord.ui.Button(label=_('art-source', ctx.author.id), style=discord.ButtonStyle.link,
                                            emoji=Emojis.Buttons.link, url=post['source'], row=2)
                    view.add_item(item=src)
                    disabled_view.add_item(item=src)
            except: True

            embed = discord.Embed(title='', description='',
                                  color=discord.Color.from_rgb(int(col[0]), int(col[1]), int(col[2])))
            embed.set_image(url=image_url)
            embed.set_author(name=f'{ctx.author.name}', icon_url=ctx.author.avatar.url)
            try:
                artist = _('art-artist', ctx.author.id).format(post["tag_string_artist"])
            except post["tag_string_artist"] == '':
                artist = ''
            except:
                artist = ''
            try:
                copyright = _('art-copyright', ctx.author.id).format(post["tag_string_copyright"])
            except post["tag_string_copyright"] == '':
                copyright = ''
            except:
                copyright = ''
            try:
                character = _('art-characters', ctx.author.id).format(post['tag_string_character'])
            except post['tag_string_character']:
                character = ''
            except:
                character = ''
            if post['source'].startswith('https://'):
                source = f"[{_('art-source', ctx.author.id)}]({post['source']})"
            else:
                source = ''

            embed.add_field(name='', value=f'''
                {filter}
                ID: **{post["id"]}**
                {_('art-rating', ctx.author.id).format(post["rating"].upper())}
                {artist}
                {character}
                {copyright}
                ''')
            return (embed, view, disabled_view)

        while sent is False:
            # if post['rating'] in ['q', 'e'] and nsfw_channel is False or post['id'] in anslist:
            #     post, iteration = GetLastPost(iteration=iteration + 1)
            if post['rating'] in ['q', 'e'] and nsfw_channel is False and value in ['1', '2']:
                anslist.append(post['id'])
                embed, view, disabled_view = getmessage(post, iteration)
                await message.edit(embed=embed, view=view)
                await asyncio.sleep(60 * 2)
                await message.edit(view=disabled_view)
                sent = True
            elif post['rating'] in ['g', 's'] and value in ['2']:
                anslist.append(post['id'])
                post, iteration = GetRandomPost(iteration=iteration + 1, tags=tag, score=score)
            elif post['rating'] in ['q', 'e'] and value in ['0']:
                anslist.append(post['id'])
                post, iteration = GetRandomPost(iteration=iteration + 1, tags=tag, score=score)
            else:
                anslist.append(post['id'])
                embed, view, disabled_view = getmessage(post, iteration)
                await message.edit(embed=embed, view=view)
                await asyncio.sleep(60 * 2)
                return await message.edit(view=disabled_view)


    @commands.hybrid_command(name='invite')
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def GetPost(self, ctx):
        '''Get Danbooru bot invite.'''
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

        embed = discord.Embed(title='', description=_('my-invite', ctx.author.id).format(invite=BotSettings.bot_invite, support=BotSettings.support_server_invite))
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)

        invite = discord.ui.Button(label=_('invite-button', ctx.author.id), style=discord.ButtonStyle.grey,
                                   emoji=Emojis.Buttons.link, url=BotSettings.bot_invite)
        support = discord.ui.Button(label=_('support-button', ctx.author.id), style=discord.ButtonStyle.red,
                                     emoji=Emojis.Buttons.link, url=BotSettings.support_server_invite)
        view = discord.ui.View()
        view.add_item(item=invite)
        view.add_item(item=support)

        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name='support')
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def GetPost(self, ctx):
        '''Get Danbooru bot invite.'''
        if CheckServer(ctx.guild, ctx.author) is False:
            class SelectMenu(discord.ui.Select):
                def __init__(self):
                    options = [(discord.SelectOption(label='English',
                                                     description='Use english language.')),
                               (discord.SelectOption(label='Русский',
                                                     description='Использовать русский язык.')), ]

                    super().__init__(placeholder='Language', min_values=1, max_values=1,
                                     options=options)

                async def callback(self, interaction: discord.Interaction):
                    if str(self.values[0]) == 'English':
                        ChangeLang(ctx.author, 'EN')
                        await interaction.response.send_message(_('changed-lang-to-EN', ctx.author.id),
                                                                ephemeral=True)
                    elif str(self.values[0]) == 'Русский':
                        ChangeLang(ctx.author, 'RU')
                        await interaction.response.send_message(_('changed-lang-to-RU', ctx.author.id),
                                                                ephemeral=True)

            view = discord.ui.View()
            view.add_item(item=SelectMenu())
            return await ctx.send(embed=UserFirstTime(ctx.author), view=view, ephemeral=True)

        CheckUser(ctx.author.id)

        embed = discord.Embed(title='',
                              description=_('my-invite', ctx.author.id).format(invite=BotSettings.bot_invite,
                                                                               support=BotSettings.support_server_invite))
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)

        invite = discord.ui.Button(label=_('invite-button', ctx.author.id), style=discord.ButtonStyle.grey,
                                   emoji=Emojis.Buttons.link, url=BotSettings.bot_invite)
        support = discord.ui.Button(label=_('support-button', ctx.author.id), style=discord.ButtonStyle.red,
                                    emoji=Emojis.Buttons.link, url=BotSettings.support_server_invite)
        view = discord.ui.View()
        view.add_item(item=invite)
        view.add_item(item=support)

        await ctx.send(embed=embed, view=view)

async def setup(client):
    await client.add_cog(Danbooru(client))