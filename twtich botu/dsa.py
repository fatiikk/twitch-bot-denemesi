import requests

api_key = "#Your API KEY"

def get_current_act():
    request_url = f"https://br.api.riotgames.com/val/content/v1/contents?locale=pt-BR&api_key={api_key}"
    response = requests.get(request_url)
    results = response.json()

    current_act = ""
    for act in results["acts"]:
        if act["isActive"] and act["type"] == 'act':
            current_act = act

    return current_act

def get_top_rank(top_size):
    current_act = get_current_act()
    request_url = f"https://api.henrikdev.xyz/valorant/v1/mmr/eu/{current_act['id']}?size={top_size}&startIndex=0&api_key={api_key}"
    response = requests.get(request_url)
    results = response.json()

    players = results["players"]

    for player in players:
        player['twitchAaccount'] = "twitch.tv"

    column_names = ["leaderboardRank", "gameName", "twitchAaccount"]
    display_column_names = ["Rank", "Nickname",  "Twitch Account"]

    return display_column_names, column_names, players

#print(get_current_act("xpremiumtr#tr1"))
print(get_top_rank("xpremiumtr#tr1"))

request_url = f"https://br.api.riotgames.com/val/ranked/v1/leaderboards/by-act/{[xpremiumtr][tr1]}

https://api.henrikdev.xyz/valorant/v1/mmr/eu/xpremiumtr/tr1

$(eval currenttierpatched=$(urlfetch json https://api.henrikdev.xyz/valorant/v1/mmr/eu/59hz fatiikk/peek).data.currenttierpatched)
