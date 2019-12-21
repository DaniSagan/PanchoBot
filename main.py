import data


if __name__ == '__main__':
    with open('token.txt') as fobj:
        token = fobj.read().strip()
    bot = data.Bot(token, 'pancho.db')
    print(bot.get_updates())
