import shutil
import json
import owlready2
import settings
from Web.set_onto import *
from Web.parsing_relaytext import *

class Web(object):
    batterbox_index = 0

    def __init__(self, resource=None):
        self.resources = resource

        owlready2.onto_path.append(settings.OWL_FILE_DIRECTORY)
        self.onto = owlready2.get_ontology(settings.OWL_FILE_NAME)

        self.onto.load()

        with open(settings.TEXT_FILE, "rt", encoding="UTF8") as data_file:
            data = json.load(data_file)

        with open(settings.BALL_TEXT_FILE, "rt", encoding="UTF8") as ball_data_file:
            self.ball_data = json.load(ball_data_file)

        self._set_game_info(data["gameInfo"])
        self._set_TeamLineUp(home=data["homeTeamLineUp"], away=data["awayTeamLineUp"])
        self.relayTexts = self._set_relayTexts(data["relayTexts"])
        self.onto.save()

    def _set_game_info(self, game_info):
        FhomeTeam = game_info["hFullName"]
        FawayTeam = game_info["aFullName"]

        homeTeam = game_info["hName"]
        awayTeam = game_info["aName"]

        homeCode = game_info["hCode"]
        awayCode = game_info["aCode"]

        date = game_info["gdate"]

        stadium = game_info["stadium"]

        self.GameInfo = {"FhomeTeam": FhomeTeam, "FawayTeam":FawayTeam, "homeTeam": homeTeam, "awayTeam": awayTeam, "stadium": stadium, "date" : date, "homeCode": homeCode, "awayCode": awayCode, "DateHomeAway" : str(date)+str(homeCode)+str(awayCode)}

        #input of ontology (game)

        self.resources.set_gameinfo(self.GameInfo)

        create_game(self.onto, self.GameInfo)
        return 1

    def _set_TeamLineUp(self, home, away):
        homeTeamPitchers = home["pitcher"]
        homeTeamBatters = home["batter"]
        homeTeamBatters.sort(key=lambda x: x["batOrder"])

        create_player(self.onto, self.GameInfo, homeTeamPitchers, isaway=0, isbatter=0)
        create_player(self.onto, self.GameInfo, homeTeamBatters, isaway=0, isbatter=1)

        awayTeamPitchers = away["pitcher"]
        awayTeamBatters = away["batter"]
        awayTeamBatters.sort(key=lambda x: x["batOrder"])

        create_player(self.onto, self.GameInfo, awayTeamPitchers, isaway=1, isbatter=0)
        create_player(self.onto, self.GameInfo, awayTeamBatters, isaway=1, isbatter=1)

        self.LineUp = {"AwayPitchers": awayTeamPitchers, "AwayBatters": awayTeamBatters, "HomePitchers": homeTeamPitchers, "HomeBatters": homeTeamBatters}
        self.resources.set_LineUp(self.LineUp)

    def _set_relayTexts(self, relayTexts):
        newlist = []
        newlist = newlist + relayTexts['1']
        newlist = newlist + relayTexts['2']
        newlist = newlist + relayTexts['3']
        newlist = newlist + relayTexts['4']
        newlist = newlist + relayTexts['5']
        newlist = newlist + relayTexts['6']
        newlist = newlist + relayTexts['7']
        newlist = newlist + relayTexts['8']
        newlist = newlist + relayTexts['9']
        newlist = newlist + relayTexts['currentBatterTexts']
        newlist = newlist + [relayTexts['currentOffensiveTeam']]
        newlist = newlist + [relayTexts['currentBatter']]

        newlist.sort(key=lambda x: x["seqno"])

        return newlist

    def parsing_relaytext(self):
        self.PB = PitchingBatting(self.GameInfo, self.LineUp, self.onto, self.resources)
        self.C = Change(self.GameInfo, self.LineUp, self.onto, self.resources)
        self.R = Result(self.GameInfo, self.LineUp, self.onto, self.resources)

        flag = 0
        for relayText in self.relayTexts:
            if (int(relayText["pitchId"].split("_")[-1]) > int(settings.START_WEB) and flag == 0):
                flag = 1
            if(flag == 1):
                next = input("next : ")

            pitchId = relayText["pitchId"]
            ball_data = self._find_ball_data_with_pitchId(pitchId)

            self.resources.set_gamescore(relayText["homeScore"], relayText["awayScore"])

            if (ball_data is None):
                if (relayText["ballcount"] == 0):  # 모든 교체(수비위치, 타석, 주자, 팀공격)
                    annotation = self.C.set(relayText)
                else:
                    annotation = self.R.set(relayText)

            else:  # pitching and batting
                annotation = self.PB.set(relayText, ball_data)

            print("from rule\t\t", annotation)
            if(flag == 1):
                self.resources.set_annotation(annotation)

    def _find_ball_data_with_pitchId(self, pitchId):
        for i in self.ball_data:
            if(pitchId == i["pitchId"]):
                return i

        return None

