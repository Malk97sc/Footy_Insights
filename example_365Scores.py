import footyIG as fty

scores = fty.Scores365()
today = scores.get_league_top_players_stats("Betplay Dimayor")
print(today.head())

cityVSvilla = "https://www.365scores.com/es-mx/football/match/premier-league-7/aston-villa-manchester-city-109-110-7#id=4147355"
game = scores.extract_statistics(cityVSvilla)
print(game.head())


