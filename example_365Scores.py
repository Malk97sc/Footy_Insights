import footyIG as fty

scores = fty.Scores365()
'''scorers = scores.get_league_top_scorers('Libertadores')
print(scorers.head())

cityVSvilla = "https://www.365scores.com/es-mx/football/match/premier-league-7/aston-villa-manchester-city-109-110-7#id=4147355"
game = scores.extract_statistics(cityVSvilla)
print(game.head())'''

leipzigVSbayern = 'https://www.365scores.com/es-mx/football/match/bundesliga-25/bayern-munich-rb-leipzig-331-7171-25#id=4168062'
stats = scores.get_players_stats(leipzigVSbayern)
print(stats.head())




