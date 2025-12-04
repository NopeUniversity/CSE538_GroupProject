import os
import glob

from datetime import datetime


def fileRead(folderPathName):
    folderPath = folderPathName.strip().strip('"').strip("'")  # tiny cleanup
    engineFileList = []

    # search .htm recursively
    for fileName in glob.glob(os.path.join(folderPath, '**', '*.htm'), recursive=True):
        with open(fileName, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
            engineFileList.append(text)
            # engineFileList.append("NEXT SET OF TEXT ...\n\n")
            print(fileName)
            print(len(text))

    # search .html recursively
    for fileName in glob.glob(os.path.join(folderPath, '**', '*.html'), recursive=True):
        with open(fileName, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
            engineFileList.append(text)
            # engineFileList.append("NEXT SET OF TEXT ...\n\n")
            print(fileName)
            print(len(text))

    return engineFileList


"""def fileRead():
    for filename in glob.glob('*.txt'):
        with open(os.path.join(os.getcwdu(), filename), 'r') as f:  # open in readonly mode
            ...
"""


def htmlToList(engineFileList):  # takes in a list of the read files with each entry of the list being an entire html text document.
    engineList = []   # contains a list of all engines and the names of the titles
    tempList = []     # used in the loop to make a list for each engine



    def _normalize_price(raw):
        # SteamDB uses cents in data-sort, e.g. "1999" -> $19.99
        try:
            if raw is None or raw == "" or raw == "-":
                return "-1"
            cents = float(raw)
            return f"{cents / 100.0:.2f}"
        except ValueError:
            return "-1"

    def _normalize_simple(raw):
        if raw is None or raw == "" or raw == "-":
            return "-1"
        return raw

    def parse_row_vals(chunk):
        """
        Given the HTML between the game name </a> and the closing </tr>,
        return all data-sort= '...' values in order.
        """
        vals = []
        marker = 'data-sort="'
        s = 0
        while True:
            pos = chunk.find(marker, s)
            if pos == -1:
                break
            vs = pos + len(marker)
            ve = chunk.find('"', vs)
            if ve == -1:
                break
            vals.append(chunk[vs:ve])
            s = ve + 1
        return vals

    for lineString in engineFileList:
        tempList.clear()

        # ----- engine name from <title> -----
        titleStart = lineString.find("<title>") + len("<title>")
        titleEnd = lineString.find(" · SteamDB")
        engine_name = lineString[titleStart:titleEnd]
        tempList.append(engine_name)

        tempPosition = titleEnd

        # ----- loop over each game row -----
        while True:
            # find the next game name link
            nameStart = lineString.find('<a class="b" href="', tempPosition)
            if nameStart == -1:
                break

            nameEnd = lineString.find('</a>', nameStart)
            tempNameChunk = lineString[nameStart + len('<a class="b" href="'):nameEnd]

            # clean ID + title
            tempNameChunk = (tempNameChunk
                             .replace('/app/', '')
                             .replace('/"', '')
                             .replace("&apos;", "'")
                             .replace("&quot;", '"'))
            gt_pos = tempNameChunk.find(">")
            tempID = tempNameChunk[:gt_pos]
            tempName = tempNameChunk[gt_pos + 1:]

            # limit ourselves to this <tr> only
            rowEnd = lineString.find('</tr>', nameEnd)
            if rowEnd == -1:
                break
            row_chunk = lineString[nameEnd:rowEnd]

            # collect all data-sort values in the row
            vals = parse_row_vals(row_chunk)
            # expected: [appid, discount, price, rating, release, follows, online, peak]
            if len(vals) < 6:
                tempPosition = rowEnd
                continue

            # work from the end so we’re robust to discount / extra columns
            price_raw   = vals[-6]  # cents
            rating_raw  = vals[-5]
            release_raw = vals[-4]
            peak_raw    = vals[-1]

            tempCost           = _normalize_price(price_raw)
            tempRating         = _normalize_simple(rating_raw)
            tempRelease        = _normalize_simple(release_raw)
            tempTopPlayerCount = _normalize_simple(peak_raw)

            tempGame = Game(tempID, tempName, tempCost,
                            tempRating, tempRelease, tempTopPlayerCount)
            tempList.append(tempGame)

            # move on to the next row
            tempPosition = rowEnd

        engineList.append(tempList.copy())

    return engineList



class Game:
    def __init__(self, id, title, cost, rating, releaseDate, topPlayerCount):
        self.id = id
        self.title = title
        try:
            # self.cost = cost
            self.cost = float(cost)
        except:
            self.cost = -1
        try:
            self.rating = float(rating)
        except:
            self.rating = -1
        # self.releaseDate = releaseDate
        try:
            # self.releaseDate = releaseDate
            self.releaseDate = datetime.fromtimestamp(int(releaseDate))
        except:
            self.releaseDate = "Unreleased"
        try:
            # self.topPlayerCount = topPlayerCount
            self.topPlayerCount = float(topPlayerCount)  # will be -1 if no top player count
        except:
            self.topPlayerCount = -1
        try:
            # self.revenueEstimate = "estimated"
            self.revenueEstimate = float(cost) * float(topPlayerCount)  # changing this to just make it quick to push
        except:
            self.revenueEstimate = -1

    def __repr__(self):
        return f"Game(id={self.id}, title={self.title!r}, cost={self.cost}, rating={self.rating}, top={self.topPlayerCount})"




# NEW HELPERS BELOW: stats + simple UI


def build_engine_dict(engineList):
    """
    Convert engineList structure:
        [ [engine_name, Game, Game, ...], [engine_name2, Game, ...], ... ]
    into a dict:
        { "Engine Name": [Game, Game, ...], ... }
    """
    engine_dict = {}
    for entry in engineList:
        if not entry:
            continue
        engine_name = entry[0]
        games = entry[1:]
        engine_dict[engine_name] = games
    return engine_dict


def _safe_avg(values):
    usable = [v for v in values if v is not None and v >= 0]
    if not usable:
        return None
    return sum(usable) / len(usable)


def _safe_max(values):
    usable = [v for v in values if v is not None and v >= 0]
    if not usable:
        return None
    return max(usable)


def compute_engine_stats(engine_name, games):
    """
    Given an engine name and its list of Game objects,
    compute averages and max for cost, rating, and top players.
    """
    costs = [g.cost for g in games]
    ratings = [g.rating for g in games]
    players = [g.topPlayerCount for g in games]

    stats = {
        "engine_name": engine_name,
        "num_games": len(games),
        "avg_cost": _safe_avg(costs),
        "max_cost": _safe_max(costs),
        "avg_rating": _safe_avg(ratings),
        "max_rating": _safe_max(ratings),
        "avg_players": _safe_avg(players),
        "max_players": _safe_max(players),
    }
    return stats


def filter_games_by_rating_range(engine_dict, min_rating, max_rating):
    """
    Return a flat list of (engine_name, Game) tuples where
    Game.rating is between min_rating and max_rating (inclusive).
    """
    results = []
    for engine_name, games in engine_dict.items():
        for g in games:
            if g.rating < 0:
                continue
            if min_rating <= g.rating <= max_rating:
                results.append((engine_name, g))
    # Sort by rating descending
    results.sort(key=lambda x: x[1].rating, reverse=True)
    return results


def compare_engines(engine_dict, engine_names):
    """
    Given a list of engine names (strings), return list of stats dicts
    for engines that exist in engine_dict.
    """
    stats_list = []
    for raw_name in engine_names:
        name = raw_name.strip()
        if not name:
            continue
        # simple case-insensitive match
        matches = [e for e in engine_dict.keys() if e.lower() == name.lower()]
        if not matches:
            continue
        engine_name = matches[0]
        games = engine_dict[engine_name]
        stats_list.append(compute_engine_stats(engine_name, games))
    return stats_list


def _fmt(v, is_money=False):
    if v is None or v < 0:
        return "N/A"
    if is_money:
        return f"${v:,.2f}"
    return f"{v:,.2f}"


def print_engine_stats(stats):
    print("\n==============================")
    print(f" Engine: {stats['engine_name']}")
    print(f" Games counted: {stats['num_games']}")
    print("------------------------------")
    print(f" Avg price:        {_fmt(stats['avg_cost'], is_money=True)}")
    print(f" Max price:        {_fmt(stats['max_cost'], is_money=True)}")
    print()
    print(f" Avg rating:       {_fmt(stats['avg_rating'])}")
    print(f" Max rating:       {_fmt(stats['max_rating'])}")
    print()
    print(f" Avg top players:  {_fmt(stats['avg_players'])}")
    print(f" Max top players:  {_fmt(stats['max_players'])}")
    print("==============================\n")


def run_ui(engine_dict):
    """
    Simple text UI that uses your parsed data + stats helpers.
    """
    engine_names = sorted(engine_dict.keys())

    while True:
        print("\n===== Game Engine Analysis UI =====")
        print("1) Look up a single engine (avg + max price, rating, players)")
        print("2) Filter games by rating range")
        print("3) Compare up to 5 engines (averages)")
        print("4) List all engine names")
        print("0) Exit")
        choice = input("Enter choice: ").strip()

        if choice == "1":
            name = input("Enter engine name (case-insensitive, partial ok): ").strip()
            name_lower = name.lower()

            # Exact or partial match
            matches = [e for e in engine_names if name_lower in e.lower()]
            if not matches:
                print("No engines found matching that name.")
                continue
            if len(matches) > 1:
                print("Multiple matches:")
                for i, e in enumerate(matches, start=1):
                    print(f"{i}. {e}")
                sel = input("Choose a number: ").strip()
                try:
                    idx = int(sel) - 1
                    if idx < 0 or idx >= len(matches):
                        print("Invalid choice.")
                        continue
                    engine_name = matches[idx]
                except ValueError:
                    print("Invalid input.")
                    continue
            else:
                engine_name = matches[0]

            stats = compute_engine_stats(engine_name, engine_dict[engine_name])
            print_engine_stats(stats)

        elif choice == "2":
            try:
                min_r = float(input("Minimum rating (0–100): ").strip())
                max_r = float(input("Maximum rating (0–100): ").strip())
            except ValueError:
                print("Invalid rating numbers.")
                continue

            if min_r > max_r:
                min_r, max_r = max_r, min_r

            results = filter_games_by_rating_range(engine_dict, min_r, max_r)
            if not results:
                print("No games found in that rating range.")
                continue

            print(f"\nGames with rating between {min_r} and {max_r}:")
            print("------------------------------------------------------------")
            for engine_name, g in results:
                print(f"[{engine_name}] {g.title} (ID {g.id}) - rating {g.rating}")
            print("------------------------------------------------------------\n")

        elif choice == "3":
            raw = input("Enter up to 5 engine names, separated by commas: ").strip()
            names = [n.strip() for n in raw.split(",") if n.strip()]
            if not names:
                print("No engine names provided.")
                continue
            if len(names) > 5:
                names = names[:5]
                print("Using first 5 engines only.")

            stats_list = compare_engines(engine_dict, names)
            if not stats_list:
                print("None of the given engines were found.")
                continue

            print("\nEngine comparison (averages):")
            print("---------------------------------------------------------------------")
            print(f"{'Engine':25s} {'Games':>6s} {'Avg $':>10s} {'Avg Rating':>12s} {'Avg Players':>14s}")
            print("---------------------------------------------------------------------")
            for s in stats_list:
                avg_cost_str = _fmt(s["avg_cost"], is_money=True)
                avg_rating_str = _fmt(s["avg_rating"])
                avg_players_str = _fmt(s["avg_players"])
                print(f"{s['engine_name'][:25]:25s} "
                      f"{s['num_games']:>6d} "
                      f"{avg_cost_str:>10s} "
                      f"{avg_rating_str:>12s} "
                      f"{avg_players_str:>14s}")
            print("---------------------------------------------------------------------\n")

        elif choice == "4":
            print("\nEngines loaded:")
            for e in engine_names:
                print("  -", e)
            print()

        elif choice == "0":
            print("Goodbye.")
            break

        else:
            print("Invalid choice, try again.")


if __name__ == '__main__':
    folderPath = input("Please input the folder path: ")
    engineFileList = fileRead(folderPath)
    engineList = htmlToList(engineFileList)

    # Build engine_dict for the UI from your existing engineList structure
    engine_dict = build_engine_dict(engineList)

    # ------------------------------------------------------------------
    # OLD DEBUG PRINTING LOOP (kept here but commented, so it's not lost)
    #
    # for list in engineList:
    #     index = 1
    #     while index < len(list):
    #         print(list[index].id)
    #         print(list[index].title)
    #         print(list[index].cost)
    #         print(list[index].rating)
    #         print(list[index].releaseDate)
    #         print(list[index].topPlayerCount)
    #         print(list[index].revenueEstimate)
    #         index += 1
    # ------------------------------------------------------------------

    # New: launch the simple text UI
    run_ui(engine_dict)
