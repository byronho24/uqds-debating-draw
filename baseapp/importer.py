from .models import Speaker
import csv


def to_bool(s):
    return s == "1"

def import_speaker_data(csv_file):
    with open(csv_file, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            speaker = Speaker()
            speaker_name_list = [row["First Name"], row["Surname"]]
            name = " ".join(speaker_name_list)
            speaker.name = name

            speaker.state_team = to_bool(row["State Team"])
            speaker.pro = to_bool(row["Pro"])
            speaker.easters_attend = to_bool(row["Easters Attend"])
            speaker.easters_break = to_bool(row["Easters Break"])
            speaker.australs_break = to_bool(row["Australs Break"])
            speaker.awdc_break = to_bool(row["AWDC Break"])
            speaker.wudc_break = to_bool(row["WUDC Break"])
            speaker.judge_break = to_bool(row["Judge Break"])
            speaker.mini_break = to_bool(row["Mini Break"])

            speaker.save()
    print("Import successful")
    return True

            