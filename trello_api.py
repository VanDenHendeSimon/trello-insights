import requests
import json
import re
import os


URI = "https://api.trello.com/1"
key = None
token = None


def get_key_and_token():
    with open("auth.json", "r") as f:
        data = json.load(f)

    return data.get("key", ""), data.get("token", "")


def get(url):
    headers = {
        "Accept": "application/json"
    }
    params = {
        "key": key,
        "token": token,
    }
    # print(url)
    return requests.get(url, headers=headers, params=params).json()


def get_board_by_name(boards, name):
    for board in boards:
        if board.get("name", "") == name:
            return board

    return None


def get_tracking_lists(lists):
    return [_list for _list in lists if "NoBurn" not in _list.get("name", "")]


def get_cards_to_track(lists):
    cards_to_complete = []
    cards_done = []

    for _list in lists:
        cards_in_list = get(f"{URI}/lists/{_list.get('id', '')}/cards")

        if _list.get("name", "").lower() == "done":
            cards_done.extend(cards_in_list)
        else:
            cards_to_complete.extend(cards_in_list)

    return cards_to_complete, cards_done


def get_inner(string):
    return string[1:-1]


def get_hours_from_cards_per_person(cards):
    hours_dict = {}

    for card in cards:
        card_name = card.get("name", "")
        member_ids = card.get("idMembers")

        try:
            this_hours_estimated = float(
                re.search(r'^.*\(([-+]?\d*\.\d+|\d+)\).*$', card_name).group(1)
            )
        except Exception:
            this_hours_estimated = 0

        try:
            this_hours_done = float(
                re.search(r'^.*\[([-+]?\d*\.\d+|\d+)\].*$', card_name).group(1)
            )
        except Exception:
            this_hours_done = 0

        for member_id in member_ids:
            if member_id in hours_dict.keys():
                hours_dict[member_id]["hours_done"] += (this_hours_done / len(member_ids))
                hours_dict[member_id]["hours_estimated"] += (this_hours_estimated / len(member_ids))
                hours_dict[member_id]["hours_remaining"] += ((this_hours_estimated - this_hours_done) / len(member_ids))
            else:
                hours_dict[member_id] = {
                    "hours_done": (this_hours_done / len(member_ids)),
                    "hours_estimated": (this_hours_estimated / len(member_ids)),
                    "hours_remaining": ((this_hours_estimated - this_hours_done) / len(member_ids)),
                }

    return hours_dict


def change_member_id_to_name(hours_dict):
    new_dict = dict()

    for member_id, hours in hours_dict.items():
        member = get(f"{URI}/members/{member_id}")
        new_dict[member.get("fullName", member.get("username", member_id)).replace("simonvdhende", "Simon Van Den Hende")] = hours

    return new_dict


def pretty_print(hours_dict):
    total_hours_planned = 0
    total_hours_done = 0
    total_hours_remaining = 0

    print("*" * 50)
    for member, hours in hours_dict.items():
        print(f"{member}:")
        print(f"Hours planned: {hours.get('hours_estimated', 0):.2f}")
        total_hours_planned += hours.get('hours_estimated', 0)

        print(f"Hours worked: {hours.get('hours_done', 0):.2f}")
        total_hours_done += hours.get('hours_done', 0)

        print(f"Hours remaining: {hours.get('hours_remaining', 0):.2f}\n")
        total_hours_remaining += hours.get('hours_remaining', 0)

    print("*" * 50)
    print(f"\nTotal hours planned: {total_hours_planned:.2f}")
    print(f"Total hours worked: {total_hours_done:.2f}")
    print(f"Total hours remaining: {total_hours_remaining:.2f}")


def main():
    global key, token
    key, token = get_key_and_token()

    boards = get(f"{URI}/members/me/boards")
    ledsrun_board = get_board_by_name(boards, "Led's Run Kanban")
    ledsrun_lists = get(f"{URI}/boards/%s/lists" % ledsrun_board.get("id", ""))

    lists_to_track = get_tracking_lists(ledsrun_lists)
    cards_to_complete, cards_done = get_cards_to_track(lists_to_track)

    hours_dict = get_hours_from_cards_per_person([*cards_to_complete, *cards_done])
    named_hours_dict = change_member_id_to_name(hours_dict)

    pretty_print(named_hours_dict)
    print(f"\n{len(cards_done)}/{len(cards_done) + len(cards_to_complete)} tickets are done")


if __name__ == '__main__':
    os.system("cls")
    main()
