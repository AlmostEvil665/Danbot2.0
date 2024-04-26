import random
import discord
from discord import default_permissions, Message, guild_only
import utils
import bingo as bingo_class
import re
import json
import pickle
import os
from discord.ext import tasks, commands
import datetime
import asyncio
import gspread
from oauth2client.service_account import ServiceAccountCredentials

ftext = "\u001b["

fnormal = "0;"
fbolt = "1;"
funderline = "4;"

fred = "31m"
fgreen = "32m"
fyellow = "33m"
fblue = "34m"
fwhite = "37m"

fend = ftext + "0m"

class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # The task will start when the bot starts
        self.create_backup.start()
        self.update_spreadsheet.start()


    @tasks.loop(hours=1)
    async def update_spreadsheet(self):
        print("Updating spreadsheet")
        teams = bingo.teams.values()

        # define the scope
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

        # add credentials to the account
        creds = ServiceAccountCredentials.from_json_keyfile_name('civil-campaign-418902-69fab8df5857.json', scope)

        try:
            client = gspread.authorize(creds)

            sheet = client.open("Fatalis Spring Bingo 2024")
            sheet_instance = sheet.get_worksheet(1)

            # sheet_instance.update_cell(2, 2, "WOrking"

            players = []

            for i, team in enumerate(sorted(teams, key=lambda team: team.points, reverse=True), start=1):
                sheet_instance.update_cell(5+i, 1, team.name)
                sheet_instance.update_cell(5+i, 2, team.points)
                for member in team.members.values():
                    players.append(member)

            for i, player in enumerate(sorted(players, key=lambda player: player.points_gained, reverse=True), start=1):
                sheet_instance.update_cell(18+i, 1, player.name)
                sheet_instance.update_cell(18+i, 2, player.points_gained)
                sheet_instance.update_cell(18+i, 3, utils.int_to_gp(player.gp_gained))
        except Exception as e:
            print(f"Updating Spreadsheet failed...\n"
                  f"=============Error============\n"
                  f"{e}")

    @tasks.loop(hours=1)
    async def create_backup(self):
        # This is the function that will be called every hour
        with open('bingo.pkl', 'wb') as f:
            pickle.dump(bingo, f)
        print(f"Successfully backed up at {datetime.datetime.now()}")

        # Get the current date and time
        now = datetime.datetime.now()

        # Format the filename
        filename = f"pickle-{now.month:02d}-{now.day:02d}-{now.hour:02d}.pkl"

        # Ensure the backups directory exists
        os.makedirs('backups', exist_ok=True)

        # Save a copy to the backups directory
        with open(os.path.join('backups', filename), 'wb') as f:
            pickle.dump(bingo, f)
        print(f"Successfully backed up to backups/{filename} at {datetime.datetime.now()}")

        # Get a list of all files in the backups directory
        files = [os.path.join('backups', f) for f in os.listdir('backups') if
                 os.path.isfile(os.path.join('backups', f))]

        # Sort the files by creation time
        files.sort(key=lambda x: os.path.getmtime(x))

        # Delete files if there are more than 24
        while len(files) > 24:
            os.remove(files[0])
            del files[0]

        print(f"Deleted a backup over 24 hours old...")

    @create_backup.before_loop
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

async def rollback_names(ctx: discord.AutocompleteContext):
    directory = "backups"
    filenames = os.listdir(directory)

    return filenames

async def boss_names(ctx: discord.AutocompleteContext):
    return ["Abyssal Sire", "Alchemical Hydra", "Artio", "Barrows Chests", "Bryophyta", "Calvar\'ion", "Callisto",
            "Cerberus", "Chambers of Xeric", "Chambers of Xeric: Challenge Mode", "Chaos Elemental", "Chaos Fanatic",
            "Commander Zilyana", "Corporeal Beast", "Crazy Archaeologist", "Dagannoth Prime", "Dagannoth Rex",
            "Dagannoth Supreme", "Deranged Archaeologist", "Duke Sucellus", "General Graardor", "Giant Mole",
            "Grotesque Guardians", "Hespori", "Kalphite Queen", "King Black Dragon", "Kraken", "Kree'Arra",
            "K'ril Tsutsaroth", "Mimic", "Nex", "Nightmare", "Phosani's Nightmare", "Obor", "Phantom Muspah",
            "Sarachnis", "Scorpia", "Scurrius", "Skotizo", "Spindel", "Tempoross", "The Gauntlet",
            "The Corrupted Gauntlet", "Leviathan", "Whisperer", "Theatre of Blood",
            "Theatre of Blood: Hard Mode", "Thermonuclear Smoke Devil", "Tombs of Amascut",
            "Tombs of Amascut: Expert Mode", "TzKal-Zuk", "TzTok-Jad", "Vardorvis", "Venenatis", "Vet'ion", "Vorkath",
            "Wintertodt", "Zalcano", "Zulrah"]


async def player_names(ctx: discord.AutocompleteContext):
    return bingo.get_player_names()


async def tile_names(ctx: discord.AutocompleteContext):
    if BINGO_TRACKING:
        return bingo.get_tile_names()
    else:
        return None


async def channel_ids(ctx: discord.AutocompleteContext):
    channel_id_list = []
    for channel in bot.get_all_channels():
        channel_id_list.append(channel.id)
    return channel_id_list


@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")


@bot.slash_command(name="sync", description="say hello to the bot")
@guild_only()
@default_permissions(manage_webhooks=True)
async def sync(ctx: discord.ApplicationContext):
    await bot.sync_commands()
    await ctx.respond("Forcing command sync")

@bot.slash_command(name="rollback", description="Rollback the memory state of the bot to a specific date and time")
@guild_only()
@default_permissions(manage_webhooks=True)
async def rollback(ctx: discord.ApplicationContext,
                   backup_filename: discord.Option(str, "Which file would you like to rollback to?", autocomplete=discord.utils.basic_autocomplete(rollback_names))):
    response = await ctx.respond("Loading backup...")
    global bingo
    with open(os.path.join('backups', backup_filename), 'wb') as f:
        pickle.dump(bingo, f)
    await response.edit_original_response(content="Loaded backup data!")

@bot.slash_command(name="save", description="Save the current state of the bot")
@guild_only()
@default_permissions(manage_webhooks=True)
async def save(ctx: discord.ApplicationContext):
    response = await ctx.respond("Saving bingo...")
    with open('bingo.pkl', 'wb') as f:
        pickle.dump(bingo, f)
    await response.edit_original_response(content="Saved all bingo data!")
@bot.slash_command(name="load", description="Load the previous state of the bot")
@guild_only()
@default_permissions(manage_webhooks=True)
async def load(ctx: discord.ApplicationContext):
    global bingo
    response = await ctx.respond("Loading bingo...")
    with open('bingo.pkl', 'rb') as f:
        bingo = pickle.load(f)
    await response.edit_original_response(content="Loaded previous bingo data!")


@bot.slash_command(name="bingo_start", description="Start tracking player data for the bingo")
@guild_only()
@default_permissions(manage_webhooks=True)
async def bingo_start(ctx: discord.ApplicationContext):
    global BINGO_TRACKING
    BINGO_TRACKING = True
    await ctx.respond("Bingo tracking started...")

@bot.slash_command(name="bingo_reset", description="Resets ALL bingo data. Tiles, players, teams, points, etc will be wiped!")
@guild_only()
@default_permissions(manage_webhooks=True)
async def bingo_start(ctx: discord.ApplicationContext):
    global bingo
    bingo = bingo_class.Bingo()
    await ctx.respond("Bingo data reset...")

@bot.slash_command(name="bingo_stop", description="Stop tracking player data for the bingo")
@guild_only()
@default_permissions(manage_webhooks=True)
async def bingo_stop(ctx: discord.ApplicationContext):
    global BINGO_TRACKING
    BINGO_TRACKING = False
    await ctx.respond("Bingo tracking stopped...")

@bot.slash_command(name="add_team", description="Adds a new team to the bingo!")
@guild_only()
@default_permissions(manage_webhooks=True)
async def new_team(ctx: discord.ApplicationContext,
                   team_name: discord.Option(str, "what is the team name?")):
    bingo.new_team(team_name)
    await ctx.respond(f"Created a new team named {team_name}!")


@bot.slash_command(name="add_player", description="Adds a player to a team in the bingo!")
@guild_only()
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
@guild_only()
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
@guild_only()
@default_permissions(manage_webhooks=True)
async def remove_player(ctx: discord.ApplicationContext,
                        player_name: discord.Option(str, "What is the players name?", autocomplete=discord.utils.basic_autocomplete(player_names))):
    player = bingo.get_player(player_name)
    del player.team.members[player_name.lower()]
    await ctx.respond(f"Successfully removed {player_name} from the bingo")


@bot.slash_command(name="remove_team", description="Removes a team from the bingo")
@guild_only()
@default_permissions(manage_webhooks=True)
async def remove_team(ctx: discord.ApplicationContext,
                      team_name: discord.Option(str, "What is the teams name?", autocomplete=discord.utils.basic_autocomplete(team_names))):
    del bingo.teams[team_name.lower()]
    await ctx.respond(f"Successfuly removed {team_name} from the bingo")

@bot.slash_command(name="award_drop", description="Adds a drop to a specific player and team")
@guild_only()
@default_permissions(manage_webhooks=True)
async def award_drop(ctx: discord.ApplicationContext,
                      player_name: discord.Option(str, "What is the players name?", autocomplete=discord.utils.basic_autocomplete(player_names)),
                      drop_name: discord.Option(str, "Must be the exact item name!!!"),
                      quantity: discord.Option(int, "How many of this item should be added?")):
    player = bingo.get_player(player_name.lower())
    tile = bingo.get_tile(drop_name)[0]
    tile.is_completed(drop_name.lower(), player)
    player.add_drop(drop_name, quantity, 0)
    await ctx.respond(f"Succesfully added {drop_name} for {player_name}")

@bot.slash_command(name="unaward_drop", description="Removes a drop from a specific player and team")
@guild_only()
@default_permissions(manage_webhooks=True)
async def unaward_drop(ctx: discord.ApplicationContext,
                      player_name: discord.Option(str, "What is the players name?", autocomplete=discord.utils.basic_autocomplete(player_names)),
                      drop_name: discord.Option(str, "Must be the exact item name!!!")):
    player = bingo.get_player(player_name.lower())
    player.remove_drop(drop_name)
    await ctx.respond(f"Succesfully removed {drop_name} for {player_name}")

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
        self.player_name = player_name.lower()
        self.team_name = team_name.lower()
        self.tile_name = tile_name.lower()

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
        channel = self.bot.get_channel(self.request.team.drop_channel)
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
@guild_only()
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
@guild_only()
@default_permissions(manage_webhooks=True)
async def add_niche_tile(ctx: discord.ApplicationContext,
                         tile_name: discord.Option(str, "What is the tile name?"),
                         points: discord.Option(float, "How many points is the tile worth?"),
                         repetition: discord.Option(int, "How many times can the tile be repeated")):
    bingo.new_niche_tile(tile_name, points, repetition)
    await ctx.respond(f"Added a tile {tile_name}!")


@bot.slash_command(name="add_drop_tile", description="A drop tile is a tile that is awarded when a drop (or any drop "
                                                     "within a list) is achieved")
@guild_only()
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

@bot.slash_command(name="add_multi_drop_tile", description="A drop tile is a tile that is awarded when a drop (or any drop "
                                                     "within a list) is achieved")
@guild_only()
@default_permissions(manage_webhooks=True)
async def add_multi_drop_tile(ctx: discord.ApplicationContext,
                        tile_name: discord.Option(str, "What is the tile name?"),
                        drops: discord.Option(str, "What drops are possible? (Enter in format: item 1/item 2/item 3"),
                        points: discord.Option(float, "How many points is this tile worth"),
                        repetition: discord.Option(int, "How many times can this tile be completed?"),
                        drops_needed: discord.Option(int, "How many times do they need to get this drop until the tile is completed?")
                        ):
    try:
        bingo.add_multi_drop_tile(tile_name, drops.split('/'), points, repetition, drops_needed)
        await ctx.respond(f"Added tile {tile_name}!")
    except Exception as e:
        await ctx.respond(f"An error occurred. If you know what went wrong then fix it. Otherwise send this junk to "
                          f"danbis:\n {e}")


@bot.slash_command(name="add_kc_tile", description="Adds a tile with a kc requirement")
@guild_only()
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
@guild_only()
@default_permissions(manage_webhooks=True)
async def add_collection_tile(ctx: discord.ApplicationContext,
                              tile_name: discord.Option(str, "What is the tile name?"),
                              collection: discord.Option(str, "Enter the collection eg(item1/item2,item3,item4"),
                              point_value: discord.Option(float, "How many points is this tile worth?"),
                              repetition: discord.Option(int, "How many times can this tile be copmleted?")):
    bingo.add_collection_tile(tile_name, point_value, repetition, collection)
    await ctx.respond("Collection tile added!")

@bot.slash_command(name='tie_tiles', description="Makes it so when one tile is completed it also completes the other. ie: The tiles are tied")
@guild_only()
@default_permissions(manage_webhooks=True)
async def add_collection_tile(ctx: discord.ApplicationContext,
                              tile_name1: discord.Option(str, "What is the tile name?", autocomplete=discord.utils.basic_autocomplete(tile_names)),
                              tile_name2: discord.Option(str, "What is the tile name?", autocomplete=discord.utils.basic_autocomplete(tile_names))):
    tile1 = bingo.game_tiles[tile_name1.lower()]
    tile2 = bingo.game_tiles[tile_name2.lower()]

    tile1.tied_tiles.append(tile2)
    tile2.tied_tiles.append(tile1)

    await ctx.respond("Tiles tied!")


@bot.slash_command(name='remove_tile', description="Removes a tile based on the tile name")
@guild_only()
@default_permissions(manage_webhooks=True)
async def remove_tile(ctx: discord.ApplicationContext,
                              tile_name: discord.Option(str, "What is the tile name", autocomplete=discord.utils.basic_autocomplete(tile_names))):
    del bingo.game_tiles[tile_name.lower()]
    await ctx.respond("Deleted Tile")


@bot.slash_command(name="award_tile", description="Awards a team and player a tile incase I made a mistake")
@guild_only()
@default_permissions(manage_webhooks=True)
async def award_tile(ctx: discord.ApplicationContext,
                     tile_name: discord.Option(str, "What is the tile name?", autocomplete=discord.utils.basic_autocomplete(tile_names)),
                     team_name: discord.Option(str, "What is the teams name?", autocomplete=discord.utils.basic_autocomplete(team_names)),
                     player_name: discord.Option(str, "What is the players name?", autocomplete=discord.utils.basic_autocomplete(player_names))):
    embed = bingo.award_tile(tile_name, team_name, player_name)
    channel = await bot.fetch_channel(bingo.teams[team_name.lower()].drop_channel)
    await channel.send(embed=embed)
    await ctx.respond("Tile awarded! Check their team channel to make sure they got the points")


@bot.slash_command(name="unaward_tile", description="Remove a tile completion and the points from a team incase I made a mistake")
@guild_only()
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
@guild_only()
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
    channel = await bot.fetch_channel(bingo.teams[team_name.lower()].drop_channel)
    await channel.send(f"Congratulations {team_name}, you have been awarded {points} points by leadership!")
    await ctx.respond(f"Awarded {team_name} {points} points!")

@bot.slash_command(name="unaward_points", description="Remove points from a team (and optionally a specific player)")
@guild_only()
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

@bot.slash_command(name="set_team_channel", description="Sets the drop channel for any given team")
@guild_only()
@default_permissions(manage_webhooks=True)
async def set_drop_channel(ctx: discord.ApplicationContext,
                           team_name: discord.Option(str, "What team are we setting the team channel for?", autocomplete=discord.utils.basic_autocomplete(team_names)),
                           channel_id: discord.Option(str, description="Copy and paste the Channel ID here")
                           ):
    team = bingo.teams[team_name.lower()]
    team.set_channel(int(channel_id))
    await ctx.respond(f"Set team drop channel successfuly! Check the team channel for my introduction")
    await utils.send_channel(bot, team.drop_channel,
                             "Welcome to the bingo! Type /help for a list of cool and useful commands")

@bot.slash_command(name="set_death_channel", description="Sets the death channel for any given team")
@guild_only()
@default_permissions(manage_webhooks=True)
async def set_death_channel(ctx: discord.ApplicationContext,
                           team_name: discord.Option(str, "What team are we setting the team channel for?", autocomplete=discord.utils.basic_autocomplete(team_names)),
                           channel_id: discord.Option(str, description="Copy and paste the Channel ID here")
                           ):
    team = bingo.teams[team_name.lower()]
    team.death_channel  = int(channel_id)
    await ctx.respond(f"Set team death channel successfuly!")

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
                team_name: discord.Option(str, "Which teams board would you like to see?", autocomplete=discord.utils.basic_autocomplete(team_names))):

    if BINGO_TRACKING:
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
    else:
        await ctx.respond("Bingo hasn't started yet so I'm not going to show you the board...")



@bot.slash_command(name="progress", description="Get your current progress on completing any given tile")
async def leaderboard(ctx: discord.ApplicationContext,
                      team_name: discord.Option(str, "What team are you checking progress for?", autocomplete=discord.utils.basic_autocomplete(team_names)),
                      tile_name: discord.Option(str, "What tile would you like to see progress for?", autocomplete=discord.utils.basic_autocomplete(tile_names))):
    team = bingo.teams[team_name.lower()]
    tile = bingo.game_tiles[tile_name.lower()]
    await ctx.respond(tile.progress(team))

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
    rankings = "```ansi\n"
    for i, team in enumerate(sorted(teams, key=lambda team: team.points, reverse=True), start=1):
        spaces_needed = 56 - len(f"Rank {i}: {team.name[:40]}") - len(f"{team.points} points ({utils.int_to_gp(team.gp_gained)})")
        # Create the string
        ansi = ""
        result = f"{ftext + fred}Rank {i}:{fend} {team.name[:40]}{' ' * spaces_needed}{ftext + fblue}{team.points} points {fend}{ftext + fgreen}({utils.int_to_gp(team.gp_gained)}){fend}\n"
        if len(rankings) + len(result) > 1021:
            break
        rankings += result
    rankings += "```"
    embed.add_field(name="Rankings", value=rankings, inline=False)

    player_rankings = "```ansi\n"
    for i, player in enumerate(sorted(players, key=lambda player: player.points_gained, reverse=True), start=1):
        spaces_needed = 56 - len(f"Rank {i}: {player.name[:40]}") - len(f"{player.points_gained} points ({utils.int_to_gp(player.gp_gained)})")
        result = f"{ftext + fred}Rank {i}: {fend}{player.name[:40]}{' ' * spaces_needed}{ftext + fblue}{player.points_gained} points {fend}{ftext + fgreen}({utils.int_to_gp(player.gp_gained)})\n{fend}"
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
    drop_rankings = "```ansi\n"
    sorted_drops = sorted(player.drops.items(), key=lambda item: item[1][1], reverse=True)
    for key, value in sorted_drops:
        spaces_needed = 56 - len(f"{value[0]} x {key}({utils.int_to_gp(value[1])})")
        result = f"{ftext + fred}{value[0]} x {fend}{key}{' ' * spaces_needed}{ftext +fgreen}({utils.int_to_gp(value[1])})\n{fend}"
        if len(drop_rankings) + len(result) > 1021:
            break
        drop_rankings += result
    drop_rankings += "```"
    embed.add_field(name="Drops", value=drop_rankings, inline=False)

    # Kill Count Rankings
    kc_rankings = "```ansi\n"
    sorted_kc = sorted(player.killcount.items(), key=lambda item: item[1], reverse=True)
    for key, value in sorted_kc:
        spaces_needed = 56 - len(f"{key}{value}")
        result = f"{ftext + fred}{key}{fend}{' ' * spaces_needed}{ftext + fblue}{value}\n{fend}"
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
        await ctx.author.send("## Step 4\n**Make sure the dink plugin is turned on!** In game chat type \"::dinkimport\"", file=stepfour_image)
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
        await ctx.respond("## Step 4\n**Make sure the dink plugin is turned on!** In game chat type \"::dinkimport\"", file=stepfour_image)
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

    most_tiles, tiles_player = 0, list(team.members.values())[0]
    most_deaths, deaths_player = 0, list(team.members.values())[0]
    most_gold, gold_player = 0, list(team.members.values())[0]

    for member in team.members.values():
        if member.tiles_completed > most_tiles:
            most_tiles = member.tiles_completed
            tiles_player = member
        if member.deaths > most_deaths:
            most_deaths = member.deaths
            deaths_player = member
        if member.gp_gained > most_gold:
            most_gold = member.gp_gained
            gold_player = member

    # Player Rankings
    players = team.members.values()
    player_rankings = "```ansi\n"
    for i, player in enumerate(sorted(players, key=lambda player: player.points_gained, reverse=True), start=1):
        spaces_needed = 56 - len(f"Rank {i}: {player.name[:40]}") - len(f"{player.points_gained} points ({utils.int_to_gp(player.gp_gained)})")
        result = f"{ftext + fred}Rank {i}:{fend} {player.name[:40]}{' ' * spaces_needed}{ftext + fblue}{player.points_gained} points {fend}{ftext + fgreen}({utils.int_to_gp(player.gp_gained)})\n{fend}"
        if len(player_rankings) + len(result) > 1021:
            break
        player_rankings += result
    player_rankings += "```"
    embed.add_field(name="Player Rankings", value=player_rankings, inline=False)

    # Drop Rankings
    drop_rankings = "```ansi\n"
    sorted_drops = sorted(team.drops.items(), key=lambda item: item[1][1], reverse=True)
    for key, value in sorted_drops:
        spaces_needed = 56 - len(f"{value[0]} x {key}({utils.int_to_gp(value[1])})")
        result = f"{ftext + fred}{value[0]} x{fend} {key}{' ' * spaces_needed}{ftext + fyellow}({utils.int_to_gp(value[1])})\n{fend}"
        if len(drop_rankings) + len(result) > 1021:
            break
        drop_rankings += result

    drop_rankings += "```"
    embed.add_field(name="Drops", value=drop_rankings, inline=False)

    # Kill Count Rankings
    kc_rankings = "```ansi\n"
    sorted_kc = sorted(team.killcount.items(), key=lambda item: item[1], reverse=True)
    for key, value in sorted_kc:
        spaces_needed = 56 - len(f"{key}{value}")
        result = f"{ftext + fred}{key}{fend}{' ' * spaces_needed}{ftext + fblue}{value}\n{fend}"
        if len(kc_rankings) + len(result) > 1021:
            break
        kc_rankings += result
    kc_rankings += "```"
    embed.add_field(name="Kill count", value=kc_rankings, inline=False)


    embed.add_field(name="Points Gained", value=f"{team.points} points", inline=True)
    embed.add_field(name="Gold Gained", value=f"{team.gp_gained} gold", inline=True)
    embed.add_field(name="Total Deaths", value=f"{team.deaths} deaths", inline=True)
    embed.add_field(name="MVP", value=f"{tiles_player.name} with {tiles_player.tiles_completed} tiles completed!", inline=False)
    embed.add_field(name="Team Thrall", value=f"{deaths_player.name} with {deaths_player.deaths} deaths!", inline=False)
    embed.add_field(name="Top G", value=f"{gold_player.name} with {gold_player.gp_gained} gold gained!", inline=False)

    await ctx.respond(embed=embed)


@bot.slash_command(name="dbg", description="This function is useful for debugging purposes")
@guild_only()
@default_permissions(manage_webhooks=True)
async def dbg(ctx: discord.ApplicationContext):
    await ctx.respond("# Bingo debug data")
    await send_large_message(ctx, str(bingo))

@bot.slash_command(name="dryness", description="Calculates how dry you are based on inputs")
async def dryness(ctx: discord.ApplicationContext,
    kill_count: discord.Option(int, "You can get your killcount from /team or /player"),
    drop_chance: discord.Option(str, "The drop chance of the item, given as a fraction"),
    obtained: discord.Option(int, "Total number of drops obtained", default=0)):

    await ctx.respond(utils.dry_calc(drop_chance, kill_count, obtained))

@bot.slash_command(name="teamdryness", description="Checks how dry your team is")
async def teamdryness(ctx: discord.ApplicationContext,
    team_name: discord.Option(str, "What is the player name?", autocomplete=discord.utils.basic_autocomplete(team_names)),
    drop_chance: discord.Option(str, "The drop chance of the item, given as a fraction"),
    boss_name: discord.Option(str, "Name of the boss you are checking dryness at", autocomplete=discord.utils.basic_autocomplete(boss_names)),
    obtained: discord.Option(int, "Total number of drops obtained", default=0)):
    kc = 0
    for player in bingo.teams[team_name.lower()].members.values():
        kc = kc + player.killcount[boss_name.lower()]

    await ctx.respond(utils.dry_calc(drop_chance, kc, obtained))


@bot.slash_command(name="help", description="Provides help information for all commands")
@guild_only()
async def help_command(ctx: discord.ApplicationContext):

    player_help_string = (
                    "**/leaderboard** - Show the current leaderboard ranking both players and teams performance\n"
                    "**/progress** - Show your current progress on completing any given tile\n"
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
                       "**/add_multi_drop_tile** - Adds a drop tile that requires you to get the drop multiple times before awarding you the tile\n"
                       "**/add_kc_tile** - Adds a kc tile. A kc tile is a bingo tile that requires a certain amount of boss kc to complete (eg: Kill mole 200 times\n"
                       "**/add_niche_tile** - Adds a niche tile. A niche tile is a bingo tile that is too niche for the bot to track automatically. This will be tracked by users submitting and admins checking submissions with /requests\n"
                       "**/remove_tile** - Removes any tile based on the tile name.\n"
                       "# Failsafe Commands\n"
                       "**/award_points** - Awards points to a given team and optionally a player\n"
                       "**/unaward_points** - Removes points from a given team and optionally a player\n"
                       "**/award_tile** - Manually awards a tile to a given team and optionally a player if the bot makes a mistake\n"
                       "**/unaward_tile** - Unawards a tile from a given team and optionally a player if the bot makes a mistake\n"
                       "**/rollback** - Rollsback the bot's memory up to 24 hours prior\n")


    # Send the embed in the response
    if ctx.author.guild_permissions.manage_webhooks:
        await ctx.respond("# Danbot Commands\n")
        await send_large_message(ctx, player_help_string + mod_help_string)
    else:
        await ctx.respond("# Danbot Commands\n")
        await ctx.respond(player_help_string)


@bot.event
async def on_message(message: Message) -> None:
    if message.author.bot and message.author.name == "Captain Hook" and BINGO_TRACKING:
        try:
            try:
                image_link = message.embeds[0].image.url
            except:
                print("No image url provided. Skipping this hook callback")
                return
            message_data = message.embeds[0].description.split('\n')
            hook_type, player_name, player = message_data[0], message_data[1], bingo.get_player(message_data[1].lower())
            if player is None:
                return

            if hook_type == "Loot Drop":
                drop_data = message_data[2:]
                for drop in drop_data:
                    try:
                        drop_name, value, quantity = utils.read_drop_data(drop)
                    except Exception as e:
                        print(e)
                    print(f"{player.name} received a drop {drop_name} x {quantity} ({value})")
                    value = utils.convert_to_int(value)
                    tiles = bingo.get_tile(drop_name)
                    player.add_drop(drop_name, int(quantity), int(value))
                    player.add_gp(value)
                    AWARDED_TILE = False
                    for tile in tiles:
                        if tile is None:
                            return
                        elif tile.completion_count[player.team.name.lower()] >= tile.recurrence:
                            player.team.image_urls[tile.name.lower()][drop_name.lower()].append(image_link)
                            continue
                        else:
                            player.team.image_urls[tile.name.lower()][drop_name.lower()].append(image_link)
                        if tile.is_completed(drop_name, player):
                            embed = bingo.award_tile(tile.name, player.team.name, player.name)
                            player.tiles_completed = player.tiles_completed + 1
                            channel = await bot.fetch_channel(player.team.drop_channel)
                            await channel.send(embed=embed)
                            AWARDED_TILE = True
                            break
                    # if not AWARDED_TILE and len(tiles) > 0:
                    #     tile = tiles[-1]
                    #     embed = bingo.repeat_tile(tile.name, player.team.name, player.name)
                    #     channel = await bot.fetch_channel(player.team.drop_channel)
                    #     await channel.send(embed=embed)
                    #     break
            if hook_type == "kc":
                boss = re.findall(r'\[(.*?)\]', message.embeds[0].description.lower().split('\n')[2])[0].lower()
                tiles = bingo.get_tile(boss)
                player.add_kc(boss)
                print(f"{player.name} killed {boss}")

                tile = None
                if len(tiles) > 0:
                    tile = tiles[0]
                else:
                    return
                player.team.image_urls[tile.name.lower()][tile.boss_name.lower()].append(image_link)
                if tile.is_completed(player.team):
                    embed = bingo.award_tile(tile.name, player.team.name, player.name)
                    player.tiles_completed = player.tiles_completed + 1
                    channel = await bot.fetch_channel(player.team.drop_channel)
                    await channel.send(embed=embed)

            if hook_type == "Death":
                player.add_death()

                descriptions = [
                    f":wing: {player.name} is in the arms of an angel :( :wing:",
                    f"{player.name} is cosplaying Toortles",
                    f"{player.name} was killed by RyGuy",
                    f":rat: sit rat :rat:",
                    f"{player.name} fell asleep probably... :sleeping:",
                    f"{player.name} is dead. Is anyone surpised?",
                    f"{player.name} is dead. Typical."
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
                        color=discord.Colour.brand_red()
                    )

                embed.set_image(url=image_link)

                channel = await bot.fetch_channel(player.team.death_channel)
                await channel.send(embed=embed)
                print(f"{player.name} has died. What a noob")
        except Exception as e:
            print(f"============Error============\n"
                  f"Error {type(e)} thrown. Caused by the following hook:\n"
                  f"{message.embeds[0].description}"
                  f"\n"
                  f"\n"
                  f"==========Error Log==========\n"
                  f"{e}")


bot.run(token=TOKEN)