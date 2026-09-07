import csv

# Ang 15 pangungusap, ayon sa pagkakasunod (u001 hanggang u015)
sentences = [
    "Pwede ba akong mag-ask kung ano yung rights ko?",
    "Hindi ko alam kung ano gagawin ko, na-involve kasi ako sa gulo.",
    "Ano po yung diversion, tsaka paano po yun nangyayari?",
    "Nahuli ako kasi nag-away kami sa labas, first time ko lang po.",
    "Pwede pa ba akong tulungan kahit minor ako?",
    "Yung mga kaibigan ko, sabi nila okay lang mag-inom pero natatakot ako.",
    "Paano ko malalaman kung anong kaso yung meron ako?",
    "Gusto ko sana mag-stop sa vices ko pero ang hirap.",
    "Ano yung mangyayari sa akin kapag under eighteen pa ako?",
    "May karapatan ba akong tumawag ng magulang ko?",
    "Natatakot ako sa pulis, hindi ko alam kung ano isasagot ko.",
    "Bakit kailangan pa ng barangay dito sa kaso ko?",
    "Sino yung pwede kong lapitan para tulungan ako?",
    "Nag-try lang po ako mag-smoking kasi na-pressure ako ng barkada.",
    "Kung sasabihin ko yung totoo, mababawasan ba yung parusa sa akin?",
]

speakers = ["s01", "s02"]

rows = []
for spk in speakers:
    for i, sentence in enumerate(sentences, 1):
        fname = f"{spk}u{i:03d}.wav"
        rows.append([fname, sentence])

with open("data/metadata.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["file_name", "transcription"])
    writer.writerows(rows)

print(f"Gawa na ang data/metadata.csv na may {len(rows)} rows.")