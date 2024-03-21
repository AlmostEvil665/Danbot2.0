from discord import Message
import discord

def convert_to_int(s) -> int:
    # Define the multipliers
    multipliers = {'k': 1000, 'm': 1000000, 'b': 1000000000}
    s = s.replace(',','')
    # If the last character of the string is a letter
    if s[-1].isalpha():
        # Get the multiplier
        multiplier = multipliers[s[-1].lower()]
        # Get the number part of the string
        number = float(s[:-1])
        # Multiply the number by the multiplier
        return int(number * multiplier)
    else:
        # If the string is just a number, convert it to an int
        return int(s)


async def send_message(message: Message, content: str) -> None:
    channel = message.channel
    await channel.send(content)


async def send_channel(bot, CHANNEL_ID, content: str) -> None:
    channel = bot.get_channel(int(CHANNEL_ID))
    if channel:
        await(channel.send(content))
    else:
        print("Channel not found")


def read_drop_data(text):
    # Split the string by ' x '
    parts = text.split(' x ')

    # The quantity is the first part
    quantity = int(parts[0])

    # The drop name is the part between brackets, remove the brackets and the 'x'
    drop_name = parts[1].split(']')[0][1:]

    # The value is the last part, remove the parentheses
    value = parts[1].split('(')[-1][:-1]

    return drop_name, value, quantity


def int_to_gp(num):
    if num >= 10 ** 9:  # Billions
        return f"{num / 10 ** 9:.2f}B"
    elif num >= 10 ** 6:  # Millions
        return f"{num / 10 ** 6:.2f}M"
    elif num >= 10 ** 3:  # Thousands
        return f"{num / 10 ** 3:.2f}K"
    else:
        return str(num)