import json, discord
from config import *

def _getserverlanguage(user_id):
    with open(Folders.users, 'r', encoding='UTF-8') as f:
        data = json.load(f)
    return str(data[str(user_id)]).split('/')[2]

def _GetText(line: str, user_id):
    lang = _getserverlanguage(user_id)
    with open(Folders.lang, 'r', encoding='UTF-8') as f:
        data = json.load(f)
    return str(data[str(line + '-' + lang)])

def UserFirstTime(user):
    embed = discord.Embed(title='Danbooru **Un**official bot.', description=FirstTime.UserWelcome.format(user.name))
    embed.set_author(name=user.name, icon_url=user.avatar.url)
    return embed


def ChangeLang(user, lang):
    with open(Folders.settings, 'r', encoding='UTF-8') as f:
        data = json.load(f)
    try:
        let = data[str(user.id)]
        data[str(user.id)] = f'channel_nsfw/channel/{lang}'
        with open(Folders.users, 'w') as f:
            json.dump(data, f)
        return f'changed-lang-to-' + lang.upper()
    except KeyError:
        data[str(user.id)] = f'channel_nsfw/channel/{lang}' # 1: channel_nsfw, 2: channel, 3: language
        with open(Folders.users, 'w') as f:
            json.dump(data, f)
        return f'changed-lang-to-' + lang.upper()

def CheckUser(user_id):
    with open(Folders.privacy, 'r', encoding='UTF-8') as f:
        data = json.load(f)
        try:
            user = data[str(user_id)]
            return True
        except KeyError:
            with open(Folders.privacy, 'w', encoding='UTF-8') as f:
                data[str(user_id)] = 'private'
                json.dump(data, f)
            return False

def CheckServer(guild, user):
    with open(Folders.users, 'r', encoding='UTF-8') as f:
        data = json.load(f)
    try:
        let = data[str(user.id)]
        return True
    except KeyError:
        with open(Folders.users, 'r', encoding='UTF-8') as f:
            towrite = json.load(f)
        if str(guild.preferred_locale).upper() == 'RU':
            language = 'RU'
        else:
            language = 'EN'
        towrite[str(user.id)] = f'channel_nsfw/channel/{language}' # 1: channel_nsfw, 2: channel, 3: language
        with open(Folders.users, 'w') as f:
            json.dump(towrite, f)
        return False

def isPrivate(user_id):
    with open(Folders.privacy, 'r', encoding='UTF-8') as f:
        data = json.load(f)
        try:
            user = data[str(user_id)]
            return user == 'private'
        except KeyError:
            with open(Folders.privacy, 'w', encoding='UTF-8') as f:
                data[str(user_id)] = 'private'
                json.dump(data, f)
            return True

def changePrivate(user_id, type):
    with open(Folders.privacy, 'r', encoding='UTF-8') as f:
        data = json.load(f)
        try:
            user = data[str(user_id)]
            with open(Folders.privacy, 'w', encoding='UTF-8') as f:
                data[str(user_id)] = type
                json.dump(data, f)
            return f'now-{type}'
        except KeyError:
            with open(Folders.privacy, 'w', encoding='UTF-8') as f:
                data[str(user_id)] = type
                json.dump(data, f)
            return f'now-{type}'

def addToFavorite(user_id, post_id):
    with open(Folders.favorites, 'r+', encoding='UTF-8') as f:
        try:
            data = json.load(f)
            user = data[f'{user_id}']
        except KeyError:
            with open(Folders.favorites, 'w', encoding='UTF-8') as f:
                data[str(user_id)] = f'{post_id}'
                json.dump(data, f)
                return 'fav-first-added'
        if str(post_id) not in user:
            with open(Folders.favorites, 'w', encoding='UTF-8') as f:
                data[str(user_id)] = f'{user};{post_id}'
                json.dump(data, f)
                return 'fav-sucessfully-added'
        else:
            return 'fav-already-in'

def removeFromFavorite(user_id, post_id):
    with open(Folders.favorites, 'r', encoding='UTF-8') as f:
        try:
            data = json.load(f)
            user = data[f'{user_id}']
            if ';' not in user:
                if post_id not in user:
                    return 'fav-remove-not-in'
                else:
                    data[f'{user_id}'] = ''
                    return 'fav-list-now-empty'
            else:
                if post_id not in user:
                    return 'fav-remove-not-in'
                else:
                    with open(Folders.favorites, 'w', encoding='UTF-8') as f:
                        list = str(data[f'{user_id}']).split(';')
                        list.remove(str(post_id))
                        data[f'{user_id}'] = ';'.join(list)
                        json.dump(data, f)
                    return 'fav-list-remove-success'
        except KeyError:
            with open(Folders.favorites, 'w', encoding='UTF-8') as f:
                data[str(user_id)] = ''
                json.dump(data, f)
                return 'fav-list-empty'
