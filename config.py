class BotSettings:
    token = ''
    application_id = 1
    public_key = ''
    status = 'WIP'
    support_server = 992082814524731443
    support_server_invite = 'https://discord.gg/8aKQu3JPAE'
    bot_invite = 'https://discord.com/api/oauth2/authorize?client_id=1030520771170271252&permissions=137439266880&scope=bot%20applications.commands'

class FirstTime:
    UserWelcome = '''
{}

:flag_us: :flag_gb: Hello, this is the first time you're using Danbooru bot. Please choose the language you want to use.

:flag_ru: Привет, это первый раз когда ты пользуешься ботом Danbooru. Выбери язык который ты хочешь использовать.

''' + f'Support: {BotSettings.support_server_invite}\n[Invite]({BotSettings.bot_invite})'



# class Danbooru:
    # DANBOORU_API_KEY = ''
    # DANBOORU_USERNAME = ''
    # You most likely dont need that.

class Folders:
    root = './'
    database = root + 'DB/'
    settings = database + 'servers.json'
    utils = root + 'utils/'
    lang = utils + 'localization.json'
    favorites = database + 'favorites.json'
    privacy = database + 'privacy.json'
    users = database + 'users.json'

class Emojis:
    class Events:
        error = ':warning:'
    class Buttons:
        refresh = '🔃'
        link = '🔗'
        favorites = '🤍'

class HyperCommands:
    Favorites = '/favorites'