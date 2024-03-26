import random
import discord
from discord import default_permissions, Message
import utils
import bingo as bingo_class
import re
import json
import pickle
from discord.ext import tasks, commands
import datetime
import asyncio

class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # The task will start when the bot starts
        self.my_background_task.start()

    @tasks.loop(hours=1)
    async def my_background_task(self):
        # This is the function that will be called every hour
        with open('bingo.pkl', 'wb') as f:
            pickle.dump(bingo, f)
        print(f"Successfully backed up at {datetime.datetime.now()}")

    @my_background_task.before_loop
    async def before_my_background_task(self):
        await self.wait_until_ready()  # wait until the bot logs in
        now = datetime.datetime.now()
        next_hour = (now.replace(minute=0, second=0, microsecond=0) + datetime.timedelta(hours=1))
        wait_seconds = (next_hour - now).total_seconds()
        await asyncio.sleep(wait_seconds)



with open('config.json') as f:
    config = json.load(f)

TOKEN = config.get('TOKEN')
intents = discord.Intents.default()
intents.messages = True
intents.typing = True
intents.message_content = True
bot = MyBot(intents=intents)
bingo = bingo_class.Bingo()
BINGO_TRACKING = True

bot.guilds.append(369695042740420608)
bot.guilds.append(1216228320807485511)


async def team_names(ctx: discord.AutocompleteContext):
    return bingo.get_team_names()


async def boss_names(ctx: discord.AutocompleteContext):
    return ["Abyssal Sire", "Alchemical Hydra", "Artio", "Barrows Chests", "Bryophyta", "Calvar\'ion", "Callisto",
            "Cerberus", "Chambers of Xeric", "Chambers of Xeric: Challenge Mode", "Chaos Elemental", "Chaos Fanatic",
            "Commander Zilyana", "Corporeal Beast", "Crazy Archaeologist", "Dagannoth Prime", "Dagannoth Rex",
            "Dagannoth Supreme", "Deranged Archaeologist", "Duke Sucellus", "General Graardor", "Giant Mole",
            "Grotesque Guardians", "Hespori", "Kalphite Queen", "King Black Dragon", "Kraken", "Kree'Arra",
            "K'ril Tsutsaroth", "Mimic", "Nex", "Nightmare", "Phosani's Nightmare", "Obor", "Phantom Muspah",
            "Sarachnis", "Scorpia", "Scurrius", "Skotizo", "Spindel", "Tempoross", "The Gauntlet",
            "The Corrupted Gauntlet", "The Leviathan", "The Whisperer", "Theatre of Blood",
            "Theatre of Blood: Hard Mode", "Thermonuclear Smoke Devil", "Tombs of Amascut",
            "Tombs of Amascut: Expert Mode", "TzKal-Zuk", "TzTok-Jad", "Vardorvis", "Venenatis", "Vet'ion", "Vorkath",
            "Wintertodt", "Zalcano", "Zulrah"]


async def player_names(ctx: discord.AutocompleteContext):
    return bingo.get_player_names()


async def tile_names(ctx: discord.AutocompleteContext):
    return bingo.get_tile_names()


async def channel_ids(ctx: discord.AutocompleteContext):
    channel_id_list = []
    for channel in bot.get_all_channels():
        channel_id_list.append(channel.id)
    return channel_id_list


@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")


@bot.slash_command(name="sync", description="say hello to the bot")
@default_permissions(manage_webhooks=True)
async def sync(ctx: discord.ApplicationContext):
    await bot.sync_commands()
    await ctx.respond("Forcing command sync")

@bot.slash_command(name="save", description="Save the current state of the bot")
@default_permissions(manage_webhooks=True)
async def save(ctx: discord.ApplicationContext):
    response = await ctx.respond("Saving bingo...")
    with open('bingo.pkl', 'wb') as f:
        pickle.dump(bingo, f)
    await response.edit_original_response(content="Saved all bingo data!")
@bot.slash_command(name="load", description="Load the previous state of the bot")
@default_permissions(manage_webhooks=True)
async def load(ctx: discord.ApplicationContext):
    global bingo
    response = await ctx.respond("Loading bingo...")
    with open('bingo.pkl', 'rb') as f:
        bingo = pickle.load(f)
    await response.edit_original_response(content="Loaded previous bingo data!")


@bot.slash_command(name="bingo_start", description="Start tracking player data for the bingo")
@default_permissions(manage_webhooks=True)
async def bingo_start(ctx: discord.ApplicationContext):
    global BINGO_TRACKING
    BINGO_TRACKING = True
    await ctx.respond("Bingo tracking started...")

@bot.slash_command(name="bingo_reset", description="Resets ALL bingo data. Tiles, players, teams, points, etc will be wiped!")
@default_permissions(manage_webhooks=True)
async def bingo_start(ctx: discord.ApplicationContext):
    global bingo
    bingo = bingo_class.Bingo()
    await ctx.respond("Bingo data reset...")

@bot.slash_command(name="bingo_stop", description="Stop tracking player data for the bingo")
@default_permissions(manage_webhooks=True)
async def bingo_stop(ctx: discord.ApplicationContext):
    global BINGO_TRACKING
    BINGO_TRACKING = False
    await ctx.respond("Bingo tracking stopped...")

@bot.slash_command(name="add_team", description="Adds a new team to the bingo!")
@default_permissions(manage_webhooks=True)
async def new_team(ctx: discord.ApplicationContext,
                   team_name: discord.Option(str, "what is the team name?")):
    bingo.new_team(team_name)
    await ctx.respond(f"Created a new team named {team_name}!")


@bot.slash_command(name="add_player", description="Adds a player to a team in the bingo!")
@default_permissions(manage_webhooks=True)
async def new_player(ctx: discord.ApplicationContext,
                     player_name: discord.Option(str, "What player are we adding?"),
                     team_name: discord.Option(str, "What team are we adding this player to?",
                                               autocomplete=discord.utils.basic_autocomplete(team_names))
                     ):
    try:
        bingo.teams[team_name].add_member(player_name)
        await ctx.respond(f"Added a player {player_name} to team {team_name}")
    except KeyError as e:
        await ctx.respond("Please input a valid team name")

@bot.slash_command(name="rename_player", description="Renames a player if they performed a name change")
async def rename_player(ctx: discord.ApplicationContext,
                        old_name: discord.Option(str, "What is your old username?", autocomplete=discord.utils.basic_autocomplete(player_names)),
                        new_name: discord.Option(str, "What is your new username")):
    player = bingo.get_player(old_name)
    team = player.team

    player.name = new_name
    del team.members[old_name.lower()]
    team.members[new_name.lower()] = player
    await ctx.respond(f"Successfully renamed {old_name} to {new_name}")

@bot.slash_command(name="rename_team", description="Renames a team if they decide they want a different name")
@default_permissions(manage_webhooks=True)
async def rename_team(ctx: discord.ApplicationContext,
                      old_name: discord.Option(str, "What is your old team name?", autocomplete=discord.utils.basic_autocomplete(team_names)),
                      new_name: discord.Option(str, "What is the new team name")):
    team = bingo.teams[old_name.lower()]
    team.name = new_name

    del bingo.teams[old_name.lower()]
    bingo.teams[new_name.lower()] = team
    await ctx.respond(f"Successfully renamed {old_name} to {new_name}")

@bot.slash_command(name="remove_player", description="Removes a player from the bingo")
@default_permissions(manage_webhooks=True)
async def remove_player(ctx: discord.ApplicationContext,
                        player_name: discord.Option(str, "What is the players name?", autocomplete=discord.utils.basic_autocomplete(player_names))):
    player = bingo.get_player(player_name)
    del player.team.members[player_name.lower()]
    await ctx.respond(f"Successfully removed {player_name} from the bingo")


@bot.slash_command(name="remove_team", description="Removes a team from the bingo")
@default_permissions(manage_webhooks=True)
async def remove_team(ctx: discord.ApplicationContext,
                      team_name: discord.Option(str, "What is the teams name?", autocomplete=discord.utils.basic_autocomplete(team_names))):
    del bingo.teams[team_name.lower()]
    await ctx.respond(f"Successfuly removed {team_name} from the bingo")

class SubmitRequestModal(discord.ui.Modal):
    def __init__(self, image, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.image = image

        self.add_item(discord.ui.InputText(label="Player name:"))
        self.add_item(discord.ui.InputText(label="Team name:"))
        self.add_item(discord.ui.InputText(label="Tile name:"))

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Confirm request")
        embed.add_field(name="Tile Name", value=self.children[2].value)
        embed.add_field(name="Team Name", value=self.children[1].value)
        embed.add_field(name="Player Name", value=self.children[0].value)
        embed.set_image(url=self.image)
        await interaction.response.send_message(embed=embed, view=SubmitRequestView(bot, self.children[0].value, self.children[1].value, self.children[2].value, self.image))

class SubmitRequestView(discord.ui.View):
    def __init__(self, bot, player_name, team_name, tile_name, image):
        super().__init__()
        self.bot = bot
        self.image = image
        self.player_name = player_name
        self.team_name = team_name
        self.tile_name = tile_name

    @discord.ui.button(label="Yes", row=0, style=discord.ButtonStyle.primary)
    async def first_button_callback(self, button, interaction):
        self.disable_all_items()
        try:
            if self.player_name.lower() not in bingo.get_player_names(): await interaction.response.edit_message(content=f"Unknown value {self.player_name} :x: ", view=None, embed=None)
            bingo.new_request(self.tile_name, self.team_name, self.player_name, self.image)
            button.label = "Your request has been submitted"
            await interaction.response.edit_message(content=f"Your request has been submitted :white_check_mark:\nAn officer will review it soon", view=None, embed= None)
        except Exception as e:
            await interaction.response.edit_message(content=f"Unknown value {e.args[0]} :x: ", view=None, embed=None)

    @discord.ui.button(label="No", row=0, style=discord.ButtonStyle.danger)
    async def second_button_callback(self, button, interaction):
        self.disable_all_items()
        button.label = "Request closed"
        await interaction.response.edit_message(view=self)


@bot.message_command(name="submit_tile")
async def submit_tile_request(ctx, message: discord.Message):
    if message.attachments:
        modal = SubmitRequestModal(message.attachments[0], title="Submit Tile Request")
        await ctx.send_modal(modal)
    else:
        image = "No image found"


class RequestView(discord.ui.View):
    def __init__(self, request, bot):
        super().__init__()
        self.request = request
        self.bot = bot

    @discord.ui.button(label="Approve", row=0, style=discord.ButtonStyle.primary)
    async def first_button_callback(self, button, interaction):
        embed = bingo.award_tile(self.request.tile.name, self.request.team.name, self.request.player_name)
        channel = self.bot.get_channel(self.request.team.channel)
        self.disable_all_items()
        await interaction.response.edit_message(content=f"You approved the request :white_check_mark:", embed=None, view=None)
        await channel.send("Your request was approved!", embed=embed, view=None)

    @discord.ui.button(label="Reject", row=0, style=discord.ButtonStyle.danger)
    async def second_button_callback(self, button, interaction):
        button.disabled = True
        self.disable_all_items()
        await interaction.response.edit_message(content="You rejected the request", embed=None, view=None)
        await interaction.response.send_message("You rejected the request :x: ")


@bot.slash_command(name="requests", description="Check if any requests need to be verified")
@default_permissions(manage_webhooks=True)
async def requests(ctx: discord.ApplicationContext):
    if len(bingo.requests) > 0:
        request = bingo.requests.pop()
        try:
            embed = discord.Embed(title="Request", colour=discord.Colour.magenta())

            embed.add_field(name="Tile Name", value=request.tile.name)
            embed.add_field(name="Team Name", value=request.team.name)
            embed.set_image(url=request.image_url)

            await ctx.respond(embed=embed, view=RequestView(request, bot))
        except:

            embed = discord.Embed(title="Request", colour=discord.Colour.magenta())

            embed.add_field(name="Tile Name", value=request.tile.name)
            embed.add_field(name="Team Name", value=request.team.name)

            embed.add_field(name="WARNING", value="Image link provided was invalid. Please contact the team captain", inline=False)
            embed.add_field(name="Proof submitted", value=request.image_url, inline=False)

            await ctx.respond(embed=embed, view=RequestView(request, bot))
    else:
        await ctx.respond("There are no requests available at the moment")

@bot.slash_command(name="add_niche_tile", description="Add a tile which cannot be tracked by Dink.")
@default_permissions(manage_webhooks=True)
async def add_niche_tile(ctx: discord.ApplicationContext,
                         tile_name: discord.Option(str, "What is the tile name?"),
                         points: discord.Option(float, "How many points is the tile worth?"),
                         repetition: discord.Option(int, "How many times can the tile be repeated")):
    bingo.new_niche_tile(tile_name, points, repetition)
    await ctx.respond(f"Added a tile {tile_name}!")


@bot.slash_command(name="add_drop_tile", description="A drop tile is a tile that is awarded when a drop (or any drop "
                                                     "within a list) is achieved")
@default_permissions(manage_webhooks=True)
async def add_drop_tile(ctx: discord.ApplicationContext,
                        tile_name: discord.Option(str, "What is the tile name?"),
                        drops: discord.Option(str, "What drops are possible? (Enter in format: item 1/item 2/item 3"),
                        points: discord.Option(float, "How many points is this tile worth"),
                        repetition: discord.Option(int, "How many times can this tile be completed?")
                        ):
    try:
        bingo.add_drop_tile(tile_name, drops.split('/'), points, repetition)
        await ctx.respond(f"Added tile {tile_name}!")
    except Exception as e:
        await ctx.respond(f"An error occurred. If you know what went wrong then fix it. Otherwise send this junk to "
                          f"danbis:\n {e}")


@bot.slash_command(name="add_kc_tile", description="Adds a tile with a kc requirement")
@default_permissions(manage_webhooks=True)
async def add_kc_tile(ctx: discord.ApplicationContext,
                      tile_name: discord.Option(str, "What is the tile name?"),
                      boss_name: discord.Option(str, "What is the boss name?",
                                                autocomplete=discord.utils.basic_autocomplete(boss_names)),
                      point_value: discord.Option(float, "How many points is this tile worth?"),
                      kill_count: discord.Option(int, "How many kills are required to finish this tile?"),
                      repetition: discord.Option(int, "How many times can this tile be completed?")):
    bingo.add_kc_tile(tile_name, boss_name, point_value, repetition, kill_count)
    await ctx.respond("Kc tile added!")


@bot.slash_command(name='add_collection_tile', description="Adds a tile with a collection requirement")
@default_permissions(manage_webhooks=True)
async def add_collection_tile(ctx: discord.ApplicationContext,
                              tile_name: discord.Option(str, "What is the tile name?"),
                              collection: discord.Option(str, "Enter the collection eg(item1/item2,item3,item4"),
                              point_value: discord.Option(float, "How many points is this tile worth?"),
                              repetition: discord.Option(int, "How many times can this tile be copmleted?")):
    bingo.add_collection_tile(tile_name, point_value, repetition, collection)
    await ctx.respond("Collection tile added!")


@bot.slash_command(name="award_tile", description="Awards a team and player a tile incase I made a mistake")
@default_permissions(manage_webhooks=True)
async def award_tile(ctx: discord.ApplicationContext,
                     tile_name: discord.Option(str, "What is the tile name?", autocomplete=discord.utils.basic_autocomplete(tile_names)),
                     team_name: discord.Option(str, "What is the teams name?", autocomplete=discord.utils.basic_autocomplete(team_names)),
                     player_name: discord.Option(str, "What is the players name?", autocomplete=discord.utils.basic_autocomplete(player_names))):
    embed = bingo.award_tile(tile_name, team_name, player_name)
    channel = ctx.guild.get_channel(bingo.teams[team_name.lower()].channel)
    await channel.send(embed=embed)
    await ctx.respond("Tile awarded! Check their team channel to make sure they got the points")


@bot.slash_command(name="unaward_tile", description="Remove a tile completion and the points from a team incase I made a mistake")
@default_permissions(manage_webhooks=True)
async def unaward_tile(ctx: discord.ApplicationContext,
                       tile_name: discord.Option(str, "What is the tile name?", autocomplete=discord.utils.basic_autocomplete(tile_names)),
                       team_name: discord.Option(str, "What is the teams name?", autocomplete=discord.utils.basic_autocomplete(team_names)),
                       player_name: discord.Option(str, "What is the players name?", autocomplete=discord.utils.basic_autocomplete(player_names))):
    try:
        bingo.unaward_tile(tile_name, team_name, player_name)
        await ctx.respond("If you are unawarding a tile due to a technical error on the bots side please direct message danbis and explain what happened. I have **NOT** notified the team they lost this tile as it is probably best for you to explain what happened.")
    except Exception as e:
        await ctx.respond(f"I ran into an error trying to unaward this tile. Here's a bunch of nonsense you should send to danbis.\n{e}")

@bot.slash_command(name="award_points", description="Award points to a given team (and optionally specific player)")
@default_permissions(manage_webhooks=True)
async def award_points(ctx: discord.ApplicationContext,
                       team_name: discord.Option(str, "What is the teams name?", autocomplete=discord.utils.basic_autocomplete(team_names)),
                       points: discord.Option(int, description="How many points are you awarding?"),
                       player_name: discord.Option(str, default="", description="What is the players name?",
                                                   autocomplete=discord.utils.basic_autocomplete(player_names)),
                       ):
    if player_name != "":
        bingo.teams[team_name.lower()].members[player_name.lower()].points_gained += points
    bingo.teams[team_name.lower()].points += points
    channel = ctx.guild.get_channel(bingo.teams[team_name.lower()].channel)
    await channel.send(f"Congratulations {team_name}, you have been awarded {points} points by leadership!")
    await ctx.respond(f"Awarded {team_name} {points} points!")

@bot.slash_command(name="unaward_points", description="Remove points from a team (and optionally a specific player)")
@default_permissions(manage_webhooks=True)
async def unaward_points(ctx:discord.ApplicationContext,
                         team_name: discord.Option(str, "What is the teams name?", autocomplete=discord.utils.basic_autocomplete(team_names)),
                         points: discord.Option(int, description="How many points are you awarding?"),
                         player_name: discord.Option(str, default="", description="What is the players name?", autocomplete=discord.utils.basic_autocomplete(player_names)),
                         ):
    if player_name != "":
        bingo.teams[team_name.lower()].members[player_name.lower()].points_gained -= points
    bingo.teams[team_name.lower()].points -= points
    await ctx.respond(f"We removed {team_name}'s points but we think it's best you explain to them why this happened. If this was a technical failure on the bot's side please message danbis and explain what happened")

@bot.slash_command(name="set_team_channel", description="Sets the text channel for any given team")
@default_permissions(manage_webhooks=True)
async def set_team_channel(ctx: discord.ApplicationContext,
                           team_name: discord.Option(str, "What team are we setting the team channel for?", autocomplete=discord.utils.basic_autocomplete(team_names)),
                           channel_id: discord.Option(str, description="Copy and paste the Channel ID here")
                           ):
    team = bingo.teams[team_name.lower()]
    team.set_channel(int(channel_id))
    await ctx.respond(f"Set team channel successfuly! Check the team channel for my introduction")
    await utils.send_channel(bot, team.channel,
                             "Welcome to the bingo! Type /help for a list of cool and useful commands")


async def send_large_message(ctx, result):
    while len(result) > 500:
        # Find the last newline character within the first 2000 characters
        split_index = result[:500].rfind('\n')

        # If there's no newline character, just split at the 2000th character
        if split_index == -1:
            split_index = 500

        # Send the chunk and remove it from the result string
        await ctx.send(result[:split_index])
        result = result[split_index:].lstrip('\n')  # remove leading newline characters

    # Send any remaining part of the string
    if result:
        await ctx.send(result)

@bot.slash_command(name="board", description="See the bingo board for your team")
async def board(ctx: discord.ApplicationContext,
                team_name: discord.Option(str, "Which teams board would you like to see?", autocomplete=team_names)):
    result_str = ""
    for tile in bingo.game_tiles.values():
        tile_data = tile.name + " - "
        for i in range(min(tile.completion_count[team_name.lower()], tile.recurrence)):
            tile_data = tile_data + ":white_check_mark:"
        for i in range(0, tile.recurrence - tile.completion_count[team_name.lower()]):
            tile_data = tile_data + ":x:"
        tile_data = tile_data + "\n"
        result_str = result_str + tile_data
    await ctx.respond("## Bingo Board\n")
    await send_large_message(ctx, result_str)





@bot.slash_command(name="leaderboard", description="Get the leaderboards / rankings of all the teams")
async def leaderboard(ctx: discord.ApplicationContext):
    # Create a new Embed object
    embed = discord.Embed(title="Leaderboards", colour=discord.Colour.yellow())

    teams = bingo.teams.values()
    players = []
    for team in teams:
        for member in team.members.values():
            players.append(member)

    # Rankings
    rankings = "```\n"
    for i, team in enumerate(sorted(teams, key=lambda team: team.points, reverse=True), start=1):
        spaces_needed = 60 - len(f"Rank {i}: {team.name[:40]}") - len(f"{team.points} points ({utils.int_to_gp(team.gp_gained)})")
        # Create the string
        result = f"Rank {i}: {team.name[:40]}{' ' * spaces_needed}{team.points} points ({utils.int_to_gp(team.gp_gained)})\n"
        if len(rankings) + len(result) > 1021:
            break
        rankings += result
    rankings += "```"
    embed.add_field(name="Rankings", value=rankings, inline=False)

    player_rankings = "```\n"
    for i, player in enumerate(sorted(players, key=lambda player: player.points_gained, reverse=True), start=1):
        spaces_needed = 60 - len(f"Rank {i}: {player.name[:40]}") - len(f"{player.points_gained} points ({utils.int_to_gp(player.gp_gained)})")
        result = f"Rank {i}: {player.name[:40]}{' ' * spaces_needed}{player.points_gained} points ({utils.int_to_gp(player.gp_gained)})\n"
        if len(player_rankings) + len(result) > 1021:
            break
        player_rankings += result

    player_rankings += "```"
    embed.add_field(name="Player Rankings", value=player_rankings, inline=False)

    await ctx.respond(embed=embed)


@bot.slash_command(name="player", description="Get a bunch of interesting data about a player!")
async def player(ctx: discord.ApplicationContext,
                 player_name: discord.Option(str, "What is the player name?", autocomplete=discord.utils.basic_autocomplete(player_names))):
    player = bingo.get_player(player_name)
    embed = discord.Embed(
        title=player.name,
        description="Here's some information about your performance",
        color=discord.Colour.yellow()
    )

    embed.add_field(name="Points Gained", value=f"{player.points_gained} points", inline=True)
    embed.add_field(name="Gold Gained", value=f"{player.gp_gained} gold", inline=True)
    embed.add_field(name="Total Deaths", value=f"{player.deaths} deaths", inline=True)

    # Drop Rankings
    drop_rankings = "```\n"
    sorted_drops = sorted(player.drops.items(), key=lambda item: item[1][1], reverse=True)
    for key, value in sorted_drops:
        spaces_needed = 60 - len(f"{value[0]} x {key}({utils.int_to_gp(value[1])})")
        result = f"{value[0]} x {key}{' ' * spaces_needed}({utils.int_to_gp(value[1])})\n"
        if len(drop_rankings) + len(result) > 1021:
            break
        drop_rankings += result
    drop_rankings += "```"
    embed.add_field(name="Drops", value=drop_rankings, inline=False)

    # Kill Count Rankings
    kc_rankings = "```\n"
    sorted_kc = sorted(player.killcount.items(), key=lambda item: item[1], reverse=True)
    for key, value in sorted_kc:
        spaces_needed = 60 - len(f"{key}{value}")
        result = f"{key}{' ' * spaces_needed}{value}\n"
        if len(kc_rankings) + len(result) > 1021:
            break
        kc_rankings += result

    kc_rankings += "```"
    embed.add_field(name="Kill count", value=kc_rankings, inline=False)

    await ctx.respond(embed=embed)

@bot.slash_command(name="dink", description="Use this command and I'll walk you through setting up the dink plugin!")
async def dink(ctx: discord.ApplicationContext):
    try:
        stepone_image = discord.File("images/dink/step1.png")
        await ctx.author.send("## Step 1\nInstall the dink plugin", file=stepone_image)
        await ctx.respond("Check your direct messages!")
        await ctx.author.send("## Step 2\nOpen this link: https://github.com/AlmostEvil665/Danbot2.0/blob/main/dink_settings.txt")
        stepthree_image = discord.File("images/dink/step3.png")
        await ctx.author.send("## Step 3\nClick \"Copy raw file\"", file=stepthree_image)
        stepfour_image = discord.File("images/dink/step4.png")
        await ctx.author.send("## Step 4\nIn game chat type \"::dinkimport\"", file=stepfour_image)
        stepfive_image = discord.File("images/dink/step5.png")
        await ctx.author.send("## Step 5\nIn the game chat channel you should see the following message (Note: you do not need to close and open the plugin settings panel despite what the message in chat says)", file=stepfive_image)
        await ctx.author.send("## Done\nYou should be all set now. If you have any questions reach out to clan leadership")
    except Exception as e:
        stepone_image = discord.File("images/dink/step1.png")
        await ctx.respond("## Step 1\nInstall the dink plugin", file=stepone_image)
        await ctx.respond("## Step 2\nOpen this link: https://github.com/AlmostEvil665/Danbot2.0/blob/main/dink_settings.txt")
        stepthree_image = discord.File("images/dink/step3.png")
        await ctx.respond("## Step 3\nClick \"Copy raw file\"", file=stepthree_image)
        stepfour_image = discord.File("images/dink/step4.png")
        await ctx.respond("## Step 4\nIn game chat type \"::dinkimport\"", file=stepfour_image)
        stepfive_image = discord.File("images/dink/step5.png")
        await ctx.respond("## Step 5\nIn the game chat channel you should see the following message (Note: you do not need to close and open the plugin settings panel despite what the message in chat says)", file=stepfive_image)
        await ctx.respond("## Done\nYou should be all set now. If you have any questions reach out to clan leadership")

@bot.slash_command(name="submit_a_tile", description="Use this command and I'll walk you through manually submitting a tile for approval")
async def submit_a_tile(ctx: discord.ApplicationContext):
    try:
        await ctx.author.send("## Step 1\nUpload an image of you completing the tile to your team text channel")
        await ctx.respond("Check your direct messages! I've sent you step by step instructions to manually submit a tile")
        step_two_image = discord.File("images/submit/step2.png")
        await ctx.author.send("## Step 2\nRight click the image, mouse over apps and select \"submit_a_tile\"", file=step_two_image)
        step_three_image = discord.File("images/submit/step3.png")
        await ctx.author.send("## Step 3\nFill out the form with your in game name, team name, and the name of the tile. These fields must be exactly correct (not case sensitive)", file=step_three_image)
        step_four_image = discord.File("images/submit/step4.png")
        await ctx.author.send("## Step 4\nCheck the confirmation page and if all the data looks correct then click \"Yes\" to send your request to clan leadership.", file=step_four_image)
        await ctx.author.send("## Step 5\nWait for clan leadership to check your request and approve it")
    except Exception as e:
        await ctx.respond("## Step 1\nUpload an image of you completing the tile to your team text channel")
        step_two_image = discord.File("images/submit/step2.png")
        await ctx.respond("## Step 2\nRight click the image, mouse over apps and select \"submit_a_tile\"", file=step_two_image)
        step_three_image = discord.File("images/submit/step3.png")
        await ctx.respond("## Step 3\nFill out the form with your in game name, team name, and the name of the tile. These fields must be exactly correct (not case sensitive)", file=step_three_image)
        step_four_image = discord.File("images/submit/step4.png")
        await ctx.respond("## Step 4\nCheck the confirmation page and if all the data looks correct then click \"Yes\" to send your request to clan leadership.", file=step_four_image)
        await ctx.respond("## Step 5\nWait for clan leadership to check your request and approve it")

@bot.slash_command(name="team", description="Get a bunch of interesting data about a team!")
async def team(ctx: discord.ApplicationContext,
               team_name: discord.Option(str, "What is the teams name?", autocomplete=discord.utils.basic_autocomplete(team_names))):
    team = bingo.teams[team_name]
    embed = discord.Embed(
        title=team.name,
        description="Here's some information about your teams performance",
        color=discord.Colour.yellow()
    )

    embed.add_field(name="Points Gained", value=f"{team.points} points", inline=True)
    embed.add_field(name="Gold Gained", value=f"{team.gp_gained} gold", inline=True)
    embed.add_field(name="Total Deaths", value=f"{team.deaths} deaths", inline=True)

    # Player Rankings
    players = team.members.values()
    player_rankings = "```\n"
    for i, player in enumerate(sorted(players, key=lambda player: player.points_gained, reverse=True), start=1):
        spaces_needed = 60 - len(f"Rank {i}: {player.name[:40]}") - len(f"{player.points_gained} points ({utils.int_to_gp(player.gp_gained)})")
        result = f"Rank {i}: {player.name[:40]}{' ' * spaces_needed}{player.points_gained} points ({utils.int_to_gp(player.gp_gained)})\n"
        if len(player_rankings) + len(result) > 1021:
            break
        player_rankings += result
    player_rankings += "```"
    embed.add_field(name="Player Rankings", value=player_rankings, inline=False)

    # Drop Rankings
    drop_rankings = "```\n"
    sorted_drops = sorted(team.drops.items(), key=lambda item: item[1][1], reverse=True)
    for key, value in sorted_drops:
        spaces_needed = 60 - len(f"{value[0]} x {key}({utils.int_to_gp(value[1])}")
        result = f"{value[0]} x {key}{' ' * spaces_needed}({utils.int_to_gp(value[1])}\n"
        if len(drop_rankings) + len(result) > 1021:
            break
        drop_rankings += result

    drop_rankings += "```"
    embed.add_field(name="Drops", value=drop_rankings, inline=False)

    # Kill Count Rankings
    kc_rankings = "```\n"
    sorted_kc = sorted(team.killcount.items(), key=lambda item: item[1], reverse=True)
    for key, value in sorted_kc:
        spaces_needed = 60 - len(f"{key}{value}")
        result = f"{key}{' ' * spaces_needed}{value}\n"
        if len(kc_rankings) + len(result) > 1021:
            break
        kc_rankings += result
    kc_rankings += "```"
    embed.add_field(name="Kill count", value=kc_rankings, inline=False)

    await ctx.respond(embed=embed)


@bot.slash_command(name="dbg", description="This function is useful for debugging purposes")
@default_permissions(manage_webhooks=True)
async def dbg(ctx: discord.ApplicationContext):
    await ctx.respond(str(bingo))


@bot.slash_command(name="help", description="Provides help information for all commands")
async def help_command(ctx: discord.ApplicationContext):

    player_help_string = (
                    "**/leaderboard** - Show the current leaderboard ranking both players and teams performance\n"
                    "**/team** - Show the performance of a specific team. This includes drops, kc, gp earned, etc\n"
                    "**/player** - Show the performance of a specific player. this includes drops, kc, gp earned, etc\n"
                    "**/rename_player** - This is used to change a players in game name\n"
                    "**/board** - Show your current progress on the bingo board\n"
                    "**/dink** - Run this command and I'll help you set up the Dink plugin\n"
                    "**/submit_a_tile** - Run this command and I'll help you manually submit a tile which requires approval by clan leadership. You'll have to use this command for any tiles I can't track automatically\n")


    mod_help_string = ("# Bingo Management\n"
                       "**/bingo_start** - Starts tracking player data for the bingo. Use this command when the bingo begins\n"
                       "**/bingo_stop** - Stops tracking player data for the bingo. Use this command when the bingo ends\n"
                       "**/bingo_reset** - Resets **ALL** bingo data. Tiles, players, teams, points, etc will be wiped!\n"
                       "# Team Management\n"
                       "**/add_team** - Adds a new team to the bingo\n"
                       "**/remove_team** - Removes a team from the bingo\n"
                       "**/rename_team** - Renames a team\n"
                       "**/set_team_channel** - Sets the text channel for a given team. I will message updates on their progress during the bingo in their respective chat channels.\n"
                       "# Player Management\n"
                       "**/add_player** - Adds a player to a given team in the bingo\n"
                       "**/remove_player** - Removes a player from a given team in the bingo\n"
                       "# Tile Management\n"
                       "**/add_collection_tile** - Adds a collection tile. A collection tile is a bingo tile that requires a collection of items to be gathered before the tile is complete (eg: complete the soul reaper axe as a team)\n"
                       "**/add_drop_tile** - Adds a drop tile. A drop tile is a bingo tile that requires one of a set of items to drop (eg: Elidinis ward/Osmuntens fang\n"
                       "**/add_kc_tile** - Adds a kc tile. A kc tile is a bingo tile that requires a certain amount of boss kc to complete (eg: Kill mole 200 times\n"
                       "**/add_niche_tile** - Adds a niche tile. A niche tile is a bingo tile that is too niche for the bot to track automatically. This will be tracked by users submitting and admins checking submissions with /requests\n"
                       "# Failsafe Commands\n"
                       "**/award_points** - Awards points to a given team and optionally a player\n"
                       "**/unaward_points** - Removes points from a given team and optionally a player\n"
                       "**/award_tile** - Manually awards a tile to a given team and optionally a player if the bot makes a mistake\n"
                       "**/unaward_tile** - Unawards a tile from a given team and optionally a player if the bot makes a mistake\n")

    # Create an embed object for a rich response
    embed = discord.Embed(title="Bot Commands", description="Here are the commands you can use with this bot:", color=discord.Color.nitro_pink())

    # Add fields to the embed for each command
    if ctx.author.guild_permissions.manage_webhooks:
        embed.add_field(name="/bingo_start", value="Start tracking player data for the bingo. Use this command when the bingo begins", inline=False)
        embed.add_field(name="/bingo_reset", value="Resets ALL bingo data. Tiles, players, teams, points, etc will be wiped!", inline=False)
        embed.add_field(name="/bingo_stop", value="Stop tracking player data for the bingo. Use this command when the bingo ends", inline=False)
        embed.add_field(name="/add_team", value="Adds a new team to the bingo!", inline=False)
        embed.add_field(name="/remove_team", value="Removes a team from the bingo", inline=False)
        embed.add_field(name="/rename_team", value="Renames a team", inline=False)
        embed.add_field(name="/set_team_channel", value="Set the text channel for a given team. We will message updates on their progress during the bingo in their respective chat channels", inline=False)
        embed.add_field(name="/add_player", value="Adds a player to a team in the bingo!", inline=False)
        embed.add_field(name="/remove_player", value="Removes a player from the bingo", inline=False)
        embed.add_field(name="/requests", value="Check if any tiles have been submitted for review. This is necessary for all *niche* tiles", inline=False)
        embed.add_field(name="/add_collection_tile", value="Adds a collection tile. A collection tile is a bingo tile that requires a collection of items to be gathered before the tile is complete (eg: complete the soul reaper axe as a team)", inline=False)
        embed.add_field(name="/add_drop_tile", value="Adds a drop tile. A drop tile is a bingo tile that requires one of a set of items to drop (eg: Elidinis ward/Osmuntens fang)", inline=False)
        embed.add_field(name="/add_kc_tile", value="Adds a kc tile. A kc tile is a bingo tile that requires a certain amount of boss kc to complete (eg: Kill mole 200 times", inline=False)
        embed.add_field(name="/add_niche_tile", value="Adds a niche tile. A niche tile is a bingo tile that is too niche for the bot to track automatically. This will be tracked by users submitting and admins checking submissions with /requests", inline=False)
        embed.add_field(name="/award_points", value="Awards points to a given team and optionally a player", inline=False)
        embed.add_field(name="/award_tile", value="Manually awards a tile to a given team and optionally a player if the bot makes a mistake", inline=False)
        embed.add_field(name="/unaward_points", value="Removes points from a given team and optionally a player", inline=False)
        embed.add_field(name="/unaward_tile", value="Unawards a tile from a given team and optionally a player if the bot makes a mistake", inline=False)

    embed.add_field(name="/leaderboard", value="Show the current leaderboard ranking both players and teams performance", inline=False)
    embed.add_field(name="/team", value="Show the performance of a specific team. This includes drops, kc, gp earned, etc", inline=False)
    embed.add_field(name="/player", value="Show the performance of a specific player. this includes drops, kc, gp earned, etc", inline=False)
    embed.add_field(name="/rename_player", value="This is used to rename a players ign", inline=False)
    embed.add_field(name="/board", value="Show your current progress on the bingo board", inline=False)


    # Send the embed in the response
    if ctx.author.guild_permissions.manage_webhooks:
        await ctx.respond("# Danbot Commands\n")
        await send_large_message(ctx, player_help_string + mod_help_string)

    else:
        await ctx.respond("# Danbot Commands\n")
        await ctx.respond(player_help_string)

@bot.slash_command(name="default", description="This creates a default bingo for testing purposes only")
@default_permissions(manage_webhooks=True)
async def default(ctx: discord.ApplicationContext):
    await new_team(ctx, "uwu")
    await set_team_channel(ctx, "uwu", 1217159356601208904)
    await new_player(ctx, "Danbis", "uwu")
    await new_player(ctx, "Ahyrexx", "uwu")
    await new_player(ctx, "Toortles", "uwu")
    await new_player(ctx, "Max uwu", "uwu")
    await add_collection_tile(ctx, f"Ardy Coll", "Iron bolts/Iron dagger, Coins", 5, 3)
    await add_drop_tile(ctx, "Thieving Tile", "Coin pouch", 5, 2)
    await add_kc_tile(ctx, "Boss", "Scurrius", 5, 1, 3)
    await add_niche_tile(ctx, "A Test Niche Tile", 5, 1)

@bot.event
async def on_message(message: Message) -> None:
    if message.author.bot and message.author.name == "Captain Hook" and BINGO_TRACKING:
        try:
            image_link = message.embeds[0].image.url
        except:
            print("No image url provided. Skipping this hook callback")
            return
        message_data = message.embeds[0].description.split('\n')
        hook_type, player_name, player = message_data[0], message_data[1], bingo.get_player(message_data[1])
        if player is None:
            return

        if hook_type == "Loot Drop":
            drop_data = message_data[2:]
            for drop in drop_data:
                try:
                    drop_name, value, quantity = utils.read_drop_data(drop)
                except Exception as e:
                    print(e)
                print(f"{player.name} recieved a drop {drop_name} x {quantity} ({value})")
                value = utils.convert_to_int(value)
                tile = bingo.get_tile(drop_name)
                player.add_drop(drop_name, int(quantity), int(value))
                player.add_gp(value)
                if tile is None: continue
                else:
                    player.team.image_urls[tile.name.lower()][drop_name.lower()].append(image_link)
                if tile.is_completed(drop_name, player):
                    embed = bingo.award_tile(tile.name, player.team.name, player.name)
                    channel = message.guild.get_channel(player.team.channel)
                    await channel.send(embed=embed)
        if hook_type == "kc":
            boss = re.findall(r'\[(.*?)\]', message.embeds[0].description.lower().split('\n')[2])[0].lower()
            tile = bingo.get_tile(boss)
            player.add_kc(boss)

            print(f"{player.name} killed {boss}")

            if tile is None: return
            player.team.image_urls[tile.name.lower()][tile.boss_name.lower()].append(image_link)
            if tile.is_completed(player.team):
                embed = bingo.award_tile(tile.name, player.team.name, player.name)
                channel = message.guild.get_channel(player.team.channel)
                await channel.send(embed=embed)

        if hook_type == "Death":
            player.add_death()

            descriptions = [
                f":wing: {player.name} is in the arms of an angel :( :wing:",
                f"{player.name} is cosplaying Toortles",
                f"{player.name} was killed by RyGuy",
                f":rat: sit rat :rat:",
                f"{player.name} fell asleep probably... :sleeping:",
                f"{player.name} is dead. Is anyone surpised?"
                f"Typical."
            ]

            embed = discord.Embed(
                title=f"{player.name} died!",
                description=random.choice(descriptions),
                color=discord.Colour.brand_red()
            )

            if player.name.lower() == "toortles":
                embed = discord.Embed(
                    title=f"{player.name} died!",
                    description=f"{player.name} is cosplaying Toortl--- oh wait thats actually toortles. Better luck next time buddy",
                    color=discord.Colour.dark_red()
                )

            embed.set_image(url=image_link)

            channel = message.guild.get_channel(player.team.channel)
            await channel.send(embed=embed)
            print(f"{player.name} has died. What a noob")


bot.run(token=TOKEN)