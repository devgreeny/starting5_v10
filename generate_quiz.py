import json, random, time
from pathlib import Path
import pandas as pd
from rapidfuzz import process, fuzz
from nba_api.stats.static import players
from nba_api.stats.endpoints import (
    leaguegamelog, boxscoretraditionalv2, boxscoresummaryv2, commonplayerinfo
)

# Load and clean NCAA D1 schools
D1_PATH = "/Users/noah/Downloads/List_of_NCAA_Division_I_institutions_2.csv"
df_d1 = pd.read_csv(D1_PATH)
df_d1 = pd.DataFrame({
    "Official": df_d1["Unnamed: 0"],
    "Common": df_d1["Unnamed: 1"],
    "Conference": df_d1["Unnamed: 7"]
})

def clean_name(name):
    return (
        name.lower()
        .replace("university of ", "")
        .replace("univ. of ", "")
        .replace("at ", "")
        .replace("the ", "")
        .replace("st.", "state")
        .replace("st ", "state ")
        .replace("state.", "state")
        .replace("-", " ")
        .replace(".", "")
        .replace("(", "")
        .replace(")", "")
        .strip()
    ) if isinstance(name, str) else ""

df_d1["Cleaned_Official"] = df_d1["Official"].apply(clean_name)
df_d1["Cleaned_Common"] = df_d1["Common"].apply(clean_name)


def match_college_to_conf(school_raw: str):
    if not school_raw or school_raw.lower().strip() in {"unknown", "none"}:
        return "Unknown", "Other", "Other"

    cleaned = clean_name(school_raw)

    match1 = process.extractOne(cleaned, df_d1["Cleaned_Official"], scorer=fuzz.token_sort_ratio)
    if match1 and match1[1] >= 85:
        row = df_d1[df_d1["Cleaned_Official"] == match1[0]].iloc[0]
        return row["Common"], "College", row["Conference"]

    match2 = process.extractOne(cleaned, df_d1["Cleaned_Common"], scorer=fuzz.token_sort_ratio)
    if match2 and match2[1] >= 85:
        row = df_d1[df_d1["Cleaned_Common"] == match2[0]].iloc[0]
        return row["Common"], "College", row["Conference"]

    if any(w in cleaned for w in ["high", "prep", "academy", "charter", "school"]):
        return school_raw, "High School", "Other"
    if any(w in cleaned for w in ["paris", "vasco", "canada", "real madrid", "bahamas", "belgrade", "france", "europe", "australia", "london", "international", "club"]):
        return school_raw, "International", "Other"

    return school_raw, "Other", "Other"


def get_college_info(player_name: str):
    match = [p for p in players.get_players() if p["full_name"].lower() == player_name.lower()]
    if not match:
        return "Unknown", "Other", "Other", None, "Unknown", "Unknown"

    player_id = match[0]["id"]
    time.sleep(0.6)
    info_df = commonplayerinfo.CommonPlayerInfo(player_id=player_id).get_data_frames()[0]
    school_raw = info_df.iloc[0].get("SCHOOL", "Unknown")
    position = info_df.iloc[0].get("POSITION", "Unknown")
    country = info_df.iloc[0].get("COUNTRY", "Unknown")
    school, school_type, conf = match_college_to_conf(school_raw)
    return school, school_type, conf, player_id, position, country


def get_all_game_ids(season: str):
    time.sleep(0.6)
    gl = leaguegamelog.LeagueGameLog(season=season, season_type_all_star="Regular Season")
    return gl.get_data_frames()[0]["GAME_ID"].unique().tolist()


def generate_quiz_from_season(season, save_dir):
    game_ids = get_all_game_ids(season)
    random.shuffle(game_ids)
    for game_id in game_ids:
        try:
            time.sleep(0.6)
            box = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id)
            df = box.get_data_frames()[0]
            starters = df[df["START_POSITION"].notna() & (df["START_POSITION"] != "")]
            if len(starters["TEAM_ID"].unique()) < 2:
                continue

            summary = boxscoresummaryv2.BoxScoreSummaryV2(game_id=game_id)
            header = summary.get_data_frames()[0].iloc[0]
            home_id, away_id = header["HOME_TEAM_ID"], header["VISITOR_TEAM_ID"]
            home_abbr = df[df["TEAM_ID"] == home_id]["TEAM_ABBREVIATION"].iloc[0]
            away_abbr = df[df["TEAM_ID"] == away_id]["TEAM_ABBREVIATION"].iloc[0]
            matchup_str = f"{away_abbr} vs {home_abbr}"

            team_lineups = []
            for team_id in [home_id, away_id]:
                team_starters = starters[starters["TEAM_ID"] == team_id].head(5)
                if len(team_starters) < 5:
                    continue

                team_abbr = team_starters["TEAM_ABBREVIATION"].iloc[0]
                opp_abbr = away_abbr if team_id == home_id else home_abbr
                t_pts = team_starters["PTS"].sum()
                t_ast = team_starters["AST"].sum()
                t_reb = team_starters["REB"].sum()
                t_def = team_starters["STL"].sum() + team_starters["BLK"].sum()

                quiz = {
                    "season": season,
                    "game_id": game_id,
                    "team_abbr": team_abbr,
                    "opponent_abbr": opp_abbr,
                    "matchup": matchup_str,
                    "players": []
                }

                for _, row in team_starters.iterrows():
                    name = row["PLAYER_NAME"]
                    school, typ, conf, pid, pos, country = get_college_info(name)
                    pts, ast, reb = row["PTS"], row["AST"], row["REB"]
                    stl, blk = row["STL"], row["BLK"]
                    defense = stl + blk

                    quiz["players"].append({
                        "name": name,
                        "school": school,
                        "school_type": typ,
                        "conference": conf,
                        "player_id": pid,
                        "position": pos,
                        "country": country,
                        "game_stats": {
                            "pts": pts, "ast": ast, "reb": reb,
                            "stl": stl, "blk": blk
                        },
                        "game_contribution_pct": {
                            "points_pct": round(pts / t_pts, 3) if t_pts else 0,
                            "assists_pct": round(ast / t_ast, 3) if t_ast else 0,
                            "rebounds_pct": round(reb / t_reb, 3) if t_reb else 0,
                            "defense_pct": round(defense / t_def, 3) if t_def else 0
                        }
                    })
                team_lineups.append(quiz)

            if team_lineups:
                selected = random.choice(team_lineups)
                out_path = Path(save_dir) / f"{selected['season']}_{selected['game_id']}_{selected['team_abbr']}.json"
                with out_path.open("w", encoding="utf-8") as f:
                    json.dump(selected, f, indent=2, ensure_ascii=False)
                print(f"Saved: {out_path}")
                return True
        except Exception as e:
            print(f"Skipping {game_id} due to: {e}")
            continue
    return False


def generate_quizzes_all_seasons():
    save_dir = Path("app/static/preloaded_quizzes")
    save_dir.mkdir(parents=True, exist_ok=True)
    seasons = [f"{year}-{str(year+1)[-2:]}" for year in range(2010, 2024)]
    saved = 0
    while saved < 30:
        season = random.choice(seasons)
        if generate_quiz_from_season(season, save_dir):
            saved += 1


if __name__ == "__main__":
    generate_quizzes_all_seasons()
