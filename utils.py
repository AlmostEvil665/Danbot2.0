from discord import Message
import discord
import math
from scipy.special import comb

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

def dry_calc(chanceTxt, kc, obtained):
    return calc(chanceTxt, kc, obtained)


def expr(x):
    x = str(x)
    x = x.replace(",", ".")
    try:
        return eval(x)
    except ValueError:
        return None

def choose(n, k):
    if k < 0 or k > n:
        return 0
    if k == 0 or k == n:
        return 1
    k = min(k, n - k)  # symmetry
    c = 1
    for i in range(k):
        c = c * (n - i) / (k - i)
    return c

def flavourText(x, obtained):
    flavourTexts = [
        [-1, 1, "You are some sort of sentient water being you're so not-dry. How'd you even do this?"],
        [1, 10, "Being this spooned would be grounds for dismissal.",
         "You might keep this drop to yourself. For your own sake"],
        [10, 20, "Only ironmen can be this lucky.", "But you got no drops, so I guess you're not an ironman."],
        [20, 30, "🥄 Spooned 🥄", "j/k you got no drops"],
        [30, 40, "Your friends will be jealous.", "...If you got any drops."],
        [40, 49, "You're quite the lucker aren't you.", "Or not, since you got no drops."],
        [49, 51, "A perfect mix of dry and undry, as all things should be."],
        [51, 61, 'Nothing interesting happens.', "Not even any drops."],
        [61, 65,
         "An unenlightened being would say 'but 1/x over x kills means I should get it', but you know better now."],
        [65, 73, 'Nothing interesting happens.', "Not even any drops."],
        [73, 74, "😂😂😂"],
        [74, 85, "oof"],
        [85, 90, "A national emergency has been declared in your drop log."],
        [90, 95, "Right, time to post on reddit."],
        [95, 99, "You after being this dry: [[File:Skeleton.png|80x80px]]"],
        [99, 99.5, "You are so dry you have collapsed into the dry singularity. The dryularity, if you will."],
        [99.5, 99.9, "The vacuum of space has more activity than your drop log."],
        [99.9, 99.99,
         "Wow that's so rare! Seems like it's bugged. We tweeted @JagexAsh for you, we're sure he'll get to the bottom of it in the next 24 hours."],
        [99.99, 1000, "Did you forget to talk to Oziach?"]

    ]
    for i in flavourTexts:
        if x >= i[0] and x <= i[1]:
            if obtained == 0 and len(i)>3:
                return i[2] + ' ' + i[3]
            return i[2]
    return ''

def calc(chanceTxt, kc, obtained):
    chance = expr(chanceTxt)
    if not chance:
        return 'Looks like there was an error with your input chance, try typing it in again'
    else:
        if chance > 1:
            return "You put your chance at over 1 you absolute madman"
        elif chance <= 0:
            return "You put your chance at 0 or negative, how you gonna get that drop?"

    kc = int(kc)
    if not kc or kc == 0:
        return "You ain't killed anything you crazy fool"
    obtained = int(obtained) or 0

    if kc < obtained:
        return 'More items dropped than things killed? how?'

    if choose(kc, obtained) == float("inf"):  # Check if we can handle these values
        return "Sorry, your killcount and obtained number combination is too large for this calculator. Try reducing your numbers."

    luck = 0.0
    for i in range(obtained + 1):
        luck = luck + comb(kc, i) * math.pow(chance, i) * math.pow(1 - chance, kc - i)
    return f"You killed {kc} monsters for an item with a {chanceTxt} ({100 * chance}%) drop chance. You had a:\n* {100 * luck}% chance of getting {obtained} drops or fewer\n* {100 * (1.0 - luck)}% chance of getting more than {obtained} drops.\n \n{flavourText((1.0 - luck) * 100, obtained)}"

