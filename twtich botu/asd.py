import discord
from discord.ext import commands
import os
import aiohttp
from replit import db
from inspect import cleandoc

# Prefix for commands
prefix = "!vc "
bot = commands.Bot(
    command_prefix=prefix,
    activity=discord.Game('Brug "!vc commands" for at se alle commands'))
url = "https://api.henrikdev.xyz/valorant"
ValoKey = os.environ['VALORANT KEY']
header = {"X-Riot-Token": ValoKey}


def split_tag(riotname):
    name = riotname.split("#")
    return name[0], name[1]


async def get_player(team, rounds_played):
    async with aiohttp.ClientSession() as session:
        team_stats = []
        for player in team:
            name = player.get("name")
            tag = player.get("tag")
            character = player.get("character")
            stats = player.get("stats")
            score = stats.get("score")
            avg_cs = score // rounds_played
            rank = player.get("currenttier_patched")

            if rank == "Unrated":
                try:
                    async with session.get(
                            f"{url}/v1/mmr/eu/{name}/{tag}") as r:
                        user_data = await r.json()
                    riotid = user_data.get("data")
                    rank = riotid.get("currenttierpatched")
                    if rank == None:
                        rank = "Unranked"
                except:
                    rank = "Unranked"
            team_stats.append([name, tag, rank, character, stats, avg_cs])
    return team_stats


# When BOT starts up
@bot.event
async def on_ready():
    # Confirm start up with print in console
    print('Logged in as: {0.user}'.format(bot))


@bot.command()
async def commands(help):
    userId = help.author.id
    user = await bot.fetch_user(str(userId))
    commands = """Du kan bruge følgende kommandoer med '!vc':
      link [USERNAME]#[TAG] - tilføje din konto til databasen for at bruge commands såsom riotid, rank og seneste.
      unlink - Fjerner din konto fra databasen.
      riotid {fx. @Discord-bruger} - Finder dit eller andens Riot ID fra databasen.
      rank {fx. @Discord-bruger} - Få din eller en andens nuværende rank og rating. Denne kommand ændre også din rank rolle.
      status - Se status på Valorant servers.
      seneste - Få detaljer om din seneste match direkte i en privat besked.
      søg [USERNAME]#[TAG] - Søg på enhver Valorant spiller i EU.
      offers - Se de nuværende skins som er på tilbud i butikken.

      [] = påkrævet
      {} = frivilligt - Virker kun hvis du har linket dit riot id"""
    await user.send(cleandoc(commands))


@bot.command()
async def status(ctx):
    # Get current status of valorant
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                    f"https://eu.api.riotgames.com/val/status/v1/platform-data",
                    header) as r:
                json_data = await r.json()
                maintenance = json_data.get("maintenances")
                incidents = json_data.get("incidents")
        except:
            return await ctx.send("Kunne ikke få status på Valorant")

    if maintenance != None:
        await ctx.send("ctx for Valorant er lige nu: " + maintenance)
    if incidents != None:
        await ctx.send("Problemer: " + incidents)
    if maintenance == None and incidents == None:
        await ctx.send("Der er ingen registeret problem med Valorant")


@bot.command()
async def offers(ctx):
    offerList = []
    skinDict = {}
    skinOnSale = []
    async with aiohttp.ClientSession() as session:
        try:
            # Get featured skins
            async with session.get(f"{url}/v1/store-featured") as r:
                try:
                    json_data = r.json()
                    data = json_data.get("data")
                    featureBundle = data.get("FeaturedBundle")
                    items = featureBundle["Bundle"]["Items"]
                except:
                    return await ctx.send(
                        "Der skete en fejl med at finde items i shoppen")
        except:
            return await ctx.send("Kunne ikke få adgang til de featured skins")

        for item in items:
            itemid = item["Item"]["ItemID"]
            offerList.append(itemid)

        try:
            # Get all skins
            async with session.get(
                    f"https://valorant-api.com/v1/weapons/skins") as r:
                skinData = await r.json()
                data = skinData.get("data")
        except:
            return await ctx.send("Kunne ikke få adgang til skins databasen")

    for item in data:
        levels = item.get("levels")
        name = levels[0].get("displayName")
        skinId = levels[0].get("uuid")
        skinDict.update({skinId: name})

    # Compare feature skin ID's with all skin ID's
    skinDictList = sorted(list(skinDict.keys()))
    for key in skinDictList:
        if key in offerList:
            skin = skinDict.get(key)
            skinOnSale.append(skin)

    if len(skinOnSale) == 0:
        return await ctx.send(
            "Kunne ikke finde nogen skins i databasen som matcher dem til salg"
        )

    # Time left of bundle
    s = featureBundle.get("BundleRemainingDurationInSeconds")
    days = int(s / 60 / 60 / 24 % 365)
    hours = int(s / 60 / 60 % 24)
    minutes = int(s / 60 % 60)
    secounds = int(s % 60)
    offer = f"""Lige nu er der følgende skins på tilbud:
    {(", ".join(skinOnSale))}.
    Tilbuddet er tilgængeligt de næste {days} dage, {hours} timer, {minutes} minutter og {secounds} sekunder.
    Skynd dig at købe dem inden de udløber!"""
    # Send the current available skins in message with timer
    await ctx.send(cleandoc(offer))


@bot.command()
async def søg(ctx, *, nameAndTag):
    try:
        username, tag = split_tag(nameAndTag)
    except:
        return await ctx.send(
            "Navn formateret forkert.\n Kommandoen skal formateres således: '!vc søg USERNAME#TAG'"
        )

    # Get info from API with username and tagline
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{url}/v1/mmr/eu/{username}/{tag}") as r:
                # Get Rank and rating from API
                accData = await r.json()
                data = accData.get("data")
                rank = data.get("currenttierpatched")
                rating = data.get("ranking_in_tier")
        except:
            return await ctx.send("Kunne ikke finde kontoen")

    await ctx.send(f"{username}#{tag} er lige nu i {rank} med {rating} rating")


@bot.command()
async def link(ctx, *, nameAndTag):
    userId = ctx.author.id

    # Check if Discord ID is already in db
    if db.keys().__contains__(str(userId)):
        return await ctx.send(
            "Der er allerede en Riot konto tilknyttet din Discord profil. Brug '!vc unlink' for at frakobel din Riot konto med din Discord profil"
        )

    try:
        username, tag = split_tag(nameAndTag)
    except:
        return await ctx.send(
            "Navn formateret forkert.\n Kommandoen skal formateres således: '!vc søg USERNAME#TAG'"
        )

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{url}/v1/account/{username}/{tag}") as r:
                data = await r.json()
                status = data.get("status")
        except:
            return await ctx.send("Kunne ikke finde kontoen")

    if status == 200:
        db[userId] = nameAndTag
        await ctx.send(
            f"Kontoen {nameAndTag} er blevet tilknyttet din Discord konto")


@bot.command()
async def unlink(ctx):
    userId = ctx.author.id
    riotId = db[str(userId)]

    # Check if Discord ID is already in db
    if not db.keys().__contains__(str(userId)):
        return await ctx.send(
            "Der er ingen Riot-konto tilknyttet din Discord-konto.")

    del db[str(userId)]
    await ctx.send(f"Din konto {riotId} er blevet slettet fra databasen.")


@bot.command()
async def rank(ctx, *, user: discord.User = None):
    if user == None:
        userId = ctx.author.id
    else:
        userId = user.id
    if not db.keys().__contains__(str(userId)):
        return await ctx.send("Discord-brugeren eksistere ikke i databasen.")

    username, tag = split_tag(db[str(userId)])

    # Get info from API with username and tagline
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{url}/v1/mmr/eu/{username}/{tag}") as r:
                try:
                    # Get Rank and rating from API
                    accData = await r.json()
                    data = accData.get("data")
                    rank = data.get("currenttierpatched")
                    rating = data.get("ranking_in_tier")
                except:
                    return await ctx.send("Kunne ikke få data fra API'en")
        except:
            return ctx.send("Kunne ikke finde kontoen")

    await ctx.send(
        f"{username}#{tag} er lige nu i {rank} med {rating} i rating")


@bot.command()
async def riotid(ctx, *, user: discord.User = None):
    if user == None:
        userId = ctx.author.id
    else:
        userId = user.id
    if not db.keys().__contains__(str(userId)):
        return await ctx.send("Discord-brugeren eksistere ikke i databasen.")

    username, tag = split_tag(db[str(userId)])

    await ctx.send(f"Riot-id'et for {ctx.author} er {username}#{tag}")


@bot.command()
async def seneste(ctx):
    userId = ctx.author.id
    if not db.keys().__contains__(str(userId)):
        return await ctx.send(
            "Din konto er ikke tilknyttet din Discord profil endnu. Brug '!vc link [USERNAME]#[TAG]' for at tilknytte din konto"
        )

    username, tag = split_tag(db[str(userId)])
    await ctx.send("Et øjeblik mens jeg henter spildataen!")

    status = await ctx.send("Status: Får data fra API")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                    f"{url}/v3/matches/eu/{username}/{tag}") as r:
                json_data = await r.json()
        except:
            return await status.edit(
                content="Status: Kunne ikke få seneste kampe")

        await status.edit(content="Status: Loader alt data")
        data = json_data.get("data")

        try:
            metadata = data[0].get("metadata")
        except:
            return await status.edit(content="Der skete en fejl, prøv igen")

        rounds_played = metadata.get("rounds_played")

        await status.edit(content="Status: Kigger hold 1 data igennem")
        red_team = await get_player(data[0]["players"]["red"], rounds_played)

        await status.edit(content="Status: Kigger hold 2 data igennem")
        blue_team = await get_player(data[0]["players"]["blue"], rounds_played)

        await status.edit(content="Status: Kigger general kampdata igennem")
        teams = data[0].get("teams")

        await status.edit(content="Status: Formater besked og sender")
        match = f"""------------------------------ MATCH SUMMARY ------------------------------
          **Hold 1:**
          {red_team[0][0]}#{red_team[0][1]} // {red_team[0][2]} // {red_team[0][3]} // K/D/A: {red_team[0][4].get("kills")}/{red_team[0][4].get("deaths")}/{red_team[0][4].get("assists")} // Combat score: {red_team[0][5]}
          {red_team[1][0]}#{red_team[1][1]} // {red_team[1][2]} // {red_team[1][3]} // K/D/A: {red_team[1][4].get("kills")}/{red_team[1][4].get("deaths")}/{red_team[1][4].get("assists")} // Combat score: {red_team[1][5]}
          {red_team[2][0]}#{red_team[2][1]} // {red_team[2][2]} // {red_team[2][3]} // K/D/A: {red_team[2][4].get("kills")}/{red_team[2][4].get("deaths")}/{red_team[2][4].get("assists")} // Combat score: {red_team[2][5]}
          {red_team[3][0]}#{red_team[3][1]} // {red_team[3][2]} // {red_team[3][3]} // K/D/A: {red_team[3][4].get("kills")}/{red_team[3][4].get("deaths")}/{red_team[3][4].get("assists")} // Combat score: {red_team[3][5]}
          {red_team[4][0]}#{red_team[4][1]} // {red_team[4][2]} // {red_team[4][3]} // K/D/A: {red_team[4][4].get("kills")}/{red_team[4][4].get("deaths")}/{red_team[4][4].get("assists")} // Combat score: {red_team[4][5]}\n

          **Hold 2:**
          {blue_team[0][0]}#{blue_team[0][1]} // {blue_team[0][2]} // {blue_team[0][3]} // K/D/A: {blue_team[0][4].get("kills")}/{blue_team[0][4].get("deaths")}/{blue_team[0][4].get("assists")} // Combat score: {blue_team[0][5]}
          {blue_team[1][0]}#{blue_team[1][1]} // {blue_team[1][2]} // {blue_team[1][3]} // K/D/A: {blue_team[1][4].get("kills")}/{blue_team[1][4].get("deaths")}/{blue_team[1][4].get("assists")} // Combat score: {blue_team[1][5]}
          {blue_team[2][0]}#{blue_team[2][1]} // {blue_team[2][2]} // {blue_team[2][3]} // K/D/A: {blue_team[2][4].get("kills")}/{blue_team[2][4].get("deaths")}/{blue_team[2][4].get("assists")} // Combat score: {blue_team[2][5]}
          {blue_team[3][0]}#{blue_team[3][1]} // {blue_team[3][2]} // {blue_team[3][3]} // K/D/A: {blue_team[3][4].get("kills")}/{blue_team[3][4].get("deaths")}/{blue_team[3][4].get("assists")} // Combat score: {blue_team[3][5]}
          {blue_team[4][0]}#{blue_team[4][1]} // {blue_team[4][2]} // {blue_team[4][3]} // K/D/A: {blue_team[4][4].get("kills")}/{blue_team[4][4].get("deaths")}/{blue_team[4][4].get("assists")} // Combat score: {blue_team[4][5]}

          Mode: {str(metadata.get("mode"))}
          Kampen sluttede {str(teams["red"]["rounds_won"])} - {str(teams["blue"]["rounds_won"])} på {str(metadata.get("map"))}"""

        user = await bot.fetch_user(str(userId))
        await user.send(cleandoc(match))
        await status.edit(content="PB sendt med kamp detaljer")


bot.run(os.getenv('DISCORD TOKEN'))