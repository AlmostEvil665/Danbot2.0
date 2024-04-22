import random
from collections import defaultdict
import pprint

import discord


def debug_print(obj):
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(obj)


def defaultdict_int():
    return defaultdict(int)



class CollectionTile:
    def __init__(self, name: str, points: float, recurrence: int, collection: list[str]):
        self.name = name
        self.points = points
        self.recurrence = recurrence
        self.collection = collection
        self.completion_count = defaultdict(int)
        self.team_drops = defaultdict(defaultdict_int)
        self.tied_tiles = []

    def progress(self, team):
        result = (f"You have completed this tile {self.completion_count[team.name.lower()]}/{self.recurrence} times.\n"
                  f"Your current progress for the next completion: \n")

        for sub_collection in self.collection:
            found = 0
            for item in sub_collection.split('/'):
                if self.team_drops[team.name.lower()][item.lower()] > 0:
                    found = found + self.team_drops[team.name.lower()][item.lower()]
            if found <= self.completion_count[team.name.lower()]:
                result = result + f"{sub_collection} :x:\n"
            else:
                result = result + f"{sub_collection} :white_check_mark:\n"

        return result

    def is_completed(self, drop_name, player):
        print("Checking copmletion on " + str(drop_name))
        self.team_drops[player.team.name.lower()][drop_name.lower()] = (
                self.team_drops[player.team.name.lower()][drop_name.lower()] + 1)

        for sub_collection in self.collection:
            found = 0
            for item in sub_collection.split('/'):
                if self.team_drops[player.team.name.lower()][item.lower()] > 0:
                    found = found + self.team_drops[player.team.name.lower()][item.lower()]
            if found <= self.completion_count[player.team.name.lower()]:
                return False
        return True


class NicheTile:
    def __init__(self, name: str, points: float, recurrence: int):
        self.name = name
        self.points = points
        self.recurrence = recurrence
        self.completion_count = defaultdict(int)
        self.tied_tiles = []


class TileRequest:
    def __init__(self, tile, image_url: str, team, player):
        self.tile = tile
        self.image_url = image_url
        self.team = team
        self.player = player
        self.tied_tiles = []


class DropTile:
    def __init__(self, name: str, drops: list[str], points: float, recurrence: int):
        self.name = name
        self.drops = drops
        self.points = points
        self.recurrence = recurrence
        self.completion_count = defaultdict(int)
        self.tied_tiles = []

    def progress(self, team):
        return f"You have completed this tile {self.completion_count[team.name.lower()]}/{self.recurrence} times"

    def is_completed(self, drop_name, player):
        return drop_name.lower() in [drop.lower() for drop in self.drops]


class MultiDropTile:
    def __init__(self, name: str, drops: list[str], points: float, recurrence: int, drops_needed: int):
        self.name = name
        self.drops = drops
        self.points = points
        self.recurrence = recurrence
        self.completion_count = defaultdict(int)
        self.drops_needed = drops_needed
        self.drops_gotten = 0
        self.tied_tiles = []

    def is_completed(self, drop_name, player):
        if drop_name.lower() in [drop.lower() for drop in self.drops]:
            self.drops_gotten = self.drops_gotten + 1
            if self.drops_gotten == self.drops_needed:
                self.drops_gotten = 0
                return True
        else:
            return False

    def progress(self, team):
        return f"You have completed this tile {self.completion_count[team.name.lower()]}/{self.recurrence} times\n You have {self.drops_gotten}/{self.drops_needed} drops needed to complete this tile"

class KcTile:
    def __init__(self, name: str, boss_name: str, points: float, recurrence: int, kc_required: int):
        self.name = name
        self.points = points
        self.boss_name = boss_name
        self.recurrence = recurrence
        self.kc_required = kc_required
        self.completion_count = defaultdict(int)
        self.tied_tiles = []

    def progress(self, team):
        return  f"You have completed this tile {self.completion_count[team.name.lower()]}/{self.recurrence} times.\n You have {team.killcount[self.boss_name.lower()]%self.kc_required}/{self.kc_required} killcount needed to complete this tile"

    def is_completed(self, team):
        return team.killcount[self.boss_name.lower()] >= self.kc_required + self.kc_required * self.completion_count[
            team.name.lower()]

def zero_tuple():
    return (0, 0)

class Player:
    def __init__(self, name: str, team):
        self.name = name
        self.points_gained = 0.0
        self.gp_gained = 0
        self.team = team
        self.deaths = 0
        self.tiles_completed = 0
        self.killcount = defaultdict(int)
        self.drops = defaultdict(zero_tuple)


    def add_death(self):
        self.deaths = self.deaths + 1
        self.team.add_deaths()

    def add_gp(self, value: int):
        self.gp_gained = self.gp_gained + value
        self.team.add_gp(value)

    def add_kc(self, bossname):
        self.killcount[bossname.lower()] = self.killcount[bossname.lower()] + 1
        self.team.killcount[bossname.lower()] = self.team.killcount[bossname.lower()] + 1

    def add_drop(self, drop_name, quantity, value):
        self.drops[drop_name.lower()] = (
            self.drops[drop_name.lower()][0] + quantity, self.drops[drop_name.lower()][1] + value)
        self.team.add_drops(drop_name, quantity, value)

    def __str__(self):
        return self.name

def defaultdict_liststr():
    return defaultdict(list[str])

class Team:
    def __init__(self, name: str):
        self.name = name
        self.members = {}
        self.points = 0.0
        self.drop_channel = 0
        self.death_channel = 0
        self.deaths = 0
        self.killcount = defaultdict(int)
        self.drops = defaultdict(zero_tuple)
        self.gp_gained = 0
        self.image_urls = defaultdict(defaultdict_liststr)

    def get_images(self, tile):
        if type(tile) is MultiDropTile:
            for drop in tile.drops:
                if self.image_urls[tile.name.lower()][drop.lower()] is not []:
                    images = self.image_urls[tile.name.lower()][drop.lower()]
                    del self.image_urls[tile.name.lower()][drop.lower()]
                    return images
        if type(tile) is DropTile:
            for drop in tile.drops:
                if self.image_urls[tile.name.lower()][drop.lower()] is not []:
                    return [self.image_urls[tile.name.lower()][drop.lower()].pop()]
        if type(tile) is KcTile:
            return [self.image_urls[tile.name.lower()][tile.boss_name.lower()][-1]]
        if type(tile) is CollectionTile:
            images = []
            for sub_collection in tile.collection:
                for item in sub_collection.split('/'):
                    if len(self.image_urls[tile.name.lower()][item.lower()]) > 0:
                        images.append(self.image_urls[tile.name.lower()][item.lower()].pop())
                        continue
            return images

    def add_member(self, player_name: str):
        player = Player(player_name, self)
        self.members[player_name.lower()] = player

    def remove_member(self, player_name: str):
        del self.players[player_name.lower()]

    def set_channel(self, channel_id: int):
        self.drop_channel = channel_id

    def add_gp(self, value):
        self.gp_gained = self.gp_gained + value

    def add_deaths(self):
        self.deaths = self.deaths + 1

    def add_drops(self, drop_name, quantity, value):
        self.drops[drop_name.lower()] = (
            self.drops[drop_name.lower()][0] + quantity, self.drops[drop_name.lower()][1] + value)


class Request:
    def __init__(self, tile, team, player_name, image_url):
        self.tile = tile
        self.team = team
        self.image_url = image_url
        self.player_name = player_name

class Bingo:
    def __init__(self):
        self.teams = {}
        self.game_tiles = {}
        self.requests = []

    def new_request(self, tile_name, team_name, player_name, proof_url):
        self.requests.append(Request(self.game_tiles[tile_name.lower()], self.teams[team_name.lower()], player_name, proof_url))

    def new_team(self, name):
        self.teams[name.lower()] = Team(name)

    def delete_team(self, name: str):
        del self.teams[name.lower()]

    def new_drops_tile(self, name, drops, points, recurrence):
        self.game_tiles[name.lower()] = DropTile(name, drops, points, recurrence)

    def new_niche_tile(self, name, points, recurrence):
        self.game_tiles[name.lower()] = NicheTile(name, points, recurrence)

    def get_player(self, player_name):
        for team in self.teams.values():
            if player_name.lower() in team.members:
                return team.members[player_name.lower()]
        return None

    def get_team_names(self):
        team_names = []
        for key in self.teams.keys():
            team_names.append(str(key))
        return team_names

    def get_player_names(self):
        player_names = []
        for team in self.teams.values():
            for key in team.members.keys():
                player_names.append(str(key))
        return player_names

    def get_tile_names(self):
        tile_names = []
        for key, value in self.game_tiles.items():
            tile_names.append(value.name)
        return tile_names

    def get_tile(self, item_name: str):
        values = []
        for key, value in self.game_tiles.items():
            if type(value) is DropTile or type(value) is MultiDropTile:
                if item_name.lower() in [drop.lower() for drop in value.drops]:
                    values.append(value)
            if type(value) is CollectionTile:
                for sub_collection in value.collection:
                    for subc_item in sub_collection.split('/'):
                        if item_name.lower() in subc_item.lower():
                            values.append(value)
            if type(value) is KcTile:
                if item_name.lower() in value.boss_name.lower():
                    values.append(value)
            if type(value) is NicheTile:
                if item_name.lower() is value.name.lower():
                    values.append(value)
        return values

    def delete_tile(self, name):
        del self.game_tiles[name.lower()]

    def unaward_tile(self, tile_name:str, team_name:str, player_name:str):
        tile = self.game_tiles[tile_name.lower()]
        team = self.teams[team_name.lower()]
        player = team.members[player_name.lower()]

        player.points_gained = player.points_gained - tile.points
        team.points = team.points - tile.points
        tile.completion_count[team.name.lower()] = tile.completion_count[team.name.lower()] - 1
        for tied_tile in tile.tied_tiles:
            tied_tile.completion_count[team_name.lower()] = tile.completion_count[team_name.lower()] - 1

    def repeat_tile(self, tile_name: str, team_name: str, player_name: str):
        try:
            tile = self.game_tiles[tile_name.lower()]
            team = self.teams[team_name.lower()]
            player = team.members[player_name.lower()]

            tile.completion_count[team_name.lower()] = tile.completion_count[team_name.lower()] + 1

            descriptions = [f"{player.name} forgot we’ve already done that tile, or are you just showing off?",
                            f"Going for a repeat performance, are we {player.name}?",
                            f"{player.name} really loves that tile I guess...",
                            f"What team are you on {player.name}?",
                            f"Bro wyd. We've done this tile {tile.completion_count[team_name.lower()]} already {player.name}."
                            ]

            embed = discord.Embed(
                title="Time wasted! You've already done this tile...",
                description=random.choice(descriptions),
                color=discord.Colour.dark_grey()
            )

            if type(tile) is not NicheTile:
                image_urls = player.team.get_images(tile)

                embed.set_image(url=image_urls[-1])

            return embed
        except Exception as e:
            print(e)

    def award_tile(self, tile_name: str, team_name: str, player_name: str):
        try:
            tile = self.game_tiles[tile_name.lower()]
            team = self.teams[team_name.lower()]
            player = team.members[player_name.lower()]

            team.points = team.points + float(tile.points)
            player.points_gained = player.points_gained + float(tile.points)
            tile.completion_count[team_name.lower()] = tile.completion_count[team_name.lower()] + 1

            for tied_tile in tile.tied_tiles:
                tied_tile.completion_count[team_name.lower()] = tile.completion_count[team_name.lower()] + 1

            embed = discord.Embed(
                title="Tile completed!",
                description=tile.name,
                color=discord.Colour.green()
            )
            embed.add_field(name="Points Gained", value=f"{tile.points} points", inline=True)
            embed.add_field(name="Player Name", value=f"{player.name}", inline=True)

            if type(tile) is not NicheTile:
                image_urls = player.team.get_images(tile)

                if len(image_urls) > 0:
                    embed.set_image(url=image_urls[0])
                    if type(tile) is not KcTile:
                        embed.add_field(name="All images (max of 5)",
                                        value=str(image_urls[-5:]).replace('\'', '').replace('[', '').replace(']', ''))

            return embed
        except Exception as e:
            print(e)

    def add_drop_tile(self, tile_name: str, drops: list[str], points: int, recurrence: int):
        self.game_tiles[tile_name.lower()] = DropTile(tile_name, drops, points, recurrence)

    def add_multi_drop_tile(self, tile_name: str, drops: list[str], points: int, recurrence: int, drops_needed: int):
        self.game_tiles[tile_name.lower()] = MultiDropTile(tile_name, drops, points, recurrence, drops_needed)

    def add_kc_tile(self, tile_name, boss_name, point_value, recurrence, kc_required):
        self.game_tiles[tile_name.lower()] = KcTile(tile_name, boss_name, int(point_value), int(recurrence),
                                                    int(kc_required))

    def add_collection_tile(self, tile_name: str, point_value: int, recurrence: int, collection: str):
        self.game_tiles[tile_name.lower()] = CollectionTile(tile_name, point_value, recurrence, collection.split(','))

    def __str__(self):
        output = "Teams\n"
        for team in self.teams.values():
            player_info = [
                f"\t\t{player.name} ({player.points_gained} points and {player.gp_gained} gold). This player has died {player.deaths} times\n"
                for player in team.members.values()]
            player_names = "".join(player_info)
            output += f"\t{team.name} ({team.points} points):\n{player_names}\n"

        output += "\nTiles\n"
        for tile in self.game_tiles.values():
            output += f"\t{tile.name}: Worth {tile.points} points {tile.recurrence} times\n"

        return output
