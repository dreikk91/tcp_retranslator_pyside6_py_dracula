from typing import List


def get_color_by_event(text_event: str) -> List[str]:
    event_guard: list = [
        "R407",
        "R417",
        "R431",
        "R470",
        "R471",
        "R472",
        "R473",
        "R474",
        "R475",
        "R401",
        "R402",
        "R403",
        "R404",
        "R405",
        "R406",
        "R408",
        "R409",
        "R442",
        "R455",
        "R454",
        "R400",
    ]
    event_disguard: list = [
        "E407",
        "E404",
        "E451",
        "E458",
        "E401",
        "E403",
        "E400",
        "E402",
        "E405",
        "E406",
        "E408",
        "E409",
        "E442",
        "E455",
        "E454",
    ]
    event_alarm: list = [
        "E100",
        "E101",
        "E110",
        "E111",
        "E112",
        "E115",
        "E116",
        "E118",
        "E120",
        "E121",
        "E122",
        "E123",
        "E124",
        "E125",
        "E130",
        "E131",
        "E132",
        "E133",
        "E134",
        "E135",
        "E136",
        "E137",
        "E138",
        "E139",
        "E140",
        "E141",
        "E142",
        "E144",
        "E145",
        "E146",
        "E150",
        "E383",
    ]
    event_ok: list = [
        "R100",
        "R101",
        "R102",
        "R110",
        "R111",
        "R112",
        "R113",
        "R114",
        "R116",
        "R117",
        "R118",
        "R120",
        "R121",
        "R122",
        "R123",
        "R124",
        "R125",
        "R126",
        "R130",
        "R131",
        "R132",
        "R133",
        "R134",
        "R135",
        "R136",
        "R137",
        "R138",
        "R139",
        "R140",
        "R141",
        "R142",
        "R143",
        "R144",
        "R145",
        "R146",
        "R147",
        "R150",
        "R151",
        "R152",
        "R153",
        "R154",
        "R155",
        "R156",
        "R157",
        "R158",
        "R159",
        "R161",
        "R162",
        "R163",
        "R200",
        "R201",
        "R202",
        "R203",
        "R204",
        "R205",
        "R206",
        "R220",
        "R300",
        "R301",
        "R302",
        "R303",
        "R304",
        "R305",
        "R306",
        "R307",
        "R308",
        "R309",
        "R310",
        "R311",
        "R312",
        "R313",
        "R314",
        "R315",
        "R319",
        "R320",
        "R321",
        "R322",
        "R323",
        "R324",
        "R325",
        "R326",
        "R327",
        "R330",
        "R331",
        "R332",
        "R333",
        "R334",
        "R335",
        "R336",
        "R337",
        "R338",
        "R339",
        "R341",
        "R342",
        "R343",
        "R344",
        "R350",
        "R351",
        "R352",
        "R353",
        "R354",
        "R355",
        "R357",
        "R358",
        "R359",
        "R361",
        "R370",
        "R371",
        "R372",
        "R373",
        "R374",
        "R375",
        "R376",
        "R377",
        "R378",
        "R380",
        "R381",
        "R382",
        "R383",
        "R384",
        "R385",
        "R386",
        "R387",
        "R388",
        "R389",
        "R391",
        "R392",
        "R393",
        "R410",
        "R411",
        "R412",
        "R413",
        "R414",
        "R415",
        "R416",
        "R421",
        "R422",
        "R423",
        "R424",
        "R425",
        "R426",
        "R427",
        "R428",
        "R429",
        "R430",
        "R432",
        "R433",
        "R434",
        "R441",
        "R450",
        "R451",
        "R452",
        "R453",
        "R456",
        "R457",
        "R458",
        "R459",
        "R461",
        "R462",
        "R463",
        "R464",
        "R465",
        "R466",
        "R501",
        "R520",
        "R521",
        "R522",
        "R523",
        "R524",
        "R525",
        "R526",
        "R527",
        "R530",
        "R531",
        "R532",
        "R551",
        "R552",
        "R553",
        "R570",
        "R571",
        "R572",
        "R573",
        "R574",
        "R575",
        "R576",
        "R577",
        "R580",
        "R581",
        "R582",
        "R583",
        "R584",
        "R585",
        "R586",
        "R601",
        "R602",
        "R603",
        "R604",
        "R605",
        "R606",
        "R607",
        "R608",
        "R609",
        "R611",
        "R612",
        "R613",
        "R614",
        "R615",
        "R616",
        "R621",
        "R622",
        "R623",
        "R625",
        "R626",
        "R627",
        "R628",
        "R629",
        "R630",
        "R631",
        "R632",
        "R641",
        "R642",
        "R654",
        "R825",
        "R826",
    ]

    other_events: list = [
        "E000",
        "E143",
        "E147",
        "E151",
        "E152",
        "E153",
        "E154",
        "E155",
        "E156",
        "E157",
        "E158",
        "E159",
        "E161",
        "E162",
        "E163",
        "E201",
        "E202",
        "E203",
        "E204",
        "E205",
        "E206",
        "E208",
        "E300",
        "E303",
        "E305",
        "E306",
        "E307",
        "E308",
        "E309",
        "E310",
        "E311",
        "E312",
        "E313",
        "E314",
        "E320",
        "E322",
        "E323",
        "E324",
        "E325",
        "E326",
        "E327",
        "E330",
        "E331",
        "E333",
        "E334",
        "E335",
        "E336",
        "E337",
        "E338",
        "E339",
        "E341",
        "E342",
        "E343",
        "E344",
        "E351",
        "E352",
        "E353",
        "E354",
        "E355",
        "E357",
        "E358",
        "E359",
        "E370",
        "E371",
        "E372",
        "E374",
        "E375",
        "E376",
        "E377",
        "E378",
        "E380",
        "E381",
        "E382",
        "E384",
        "E385",
        "E386",
        "E387",
        "E388",
        "E389",
        "E391",
        "E392",
        "E393",
        "E410",
        "E411",
        "E412",
        "E413",
        "E414",
        "E415",
        "E416",
        "E421",
        "E422",
        "E424",
        "E425",
        "E426",
        "E427",
        "E428",
        "E429",
        "E430",
        "E432",
        "E433",
        "E434",
        "E450",
        "E453",
        "E457",
        "E461",
        "E462",
        "E464",
        "E465",
        "E501",
        "E522",
        "E523",
        "E524",
        "E525",
        "E526",
        "E527",
        "E528",
        "E530",
        "E531",
        "E532",
        "E551",
        "E552",
        "E553",
        "E571",
        "E572",
        "E573",
        "E574",
        "E575",
        "E576",
        "E577",
        "E584",
        "E600",
        "E601",
        "E602",
        "E603",
        "E604",
        "E605",
        "E606",
        "E607",
        "E608",
        "E609",
        "E610",
        "E611",
        "E612",
        "E613",
        "E614",
        "E615",
        "E616",
        "E621",
        "E622",
        "E623",
        "E625",
        "E626",
        "E627",
        "E628",
        "E629",
        "E630",
        "E631",
        "E632",
        "E641",
        "E642",
        "E654",
        "E656",
        "E800",
        "E830",
    ]

    if text_event in event_guard:
        return ["#2980b9", "#ecf0f1"]
    elif text_event in event_disguard:
        return ["#27ae60", "#ecf0f1"]
    elif text_event in event_ok:
        return ["#f1c40f", "#2c3e50"]
    elif text_event in event_alarm:
        return ["#e74c3c", "#ecf0f1"]
    elif text_event in event_guard:
        return ["#2980b9", "#ecf0f1"]
    elif text_event in event_disguard:
        return ["#27ae60", "#ecf0f1"]
    elif text_event in other_events:
        return ["#ecf0f1", "#2c3e50"]
    else:
        return ["#ecf0f1", "#2c3e50"]


event_guard: list = [
    "R407",
    "R417",
    "R431",
    "R470",
    "R471",
    "R472",
    "R473",
    "R474",
    "R475",
    "R401",
    "R402",
    "R403",
    "R404",
    "R405",
    "R406",
    "R408",
    "R409",
    "R442",
    "R455",
    "R454",
    "R400",
]
event_disguard: list = [
    "E407",
    "E404",
    "E451",
    "E458",
    "E401",
    "E403",
    "E400",
    "E402",
    "E405",
    "E406",
    "E408",
    "E409",
    "E442",
    "E455",
    "E454",
]
event_alarm: list = [
    "E100",
    "E101",
    "E110",
    "E111",
    "E112",
    "E115",
    "E116",
    "E118",
    "E120",
    "E121",
    "E122",
    "E123",
    "E124",
    "E125",
    "E130",
    "E131",
    "E132",
    "E133",
    "E134",
    "E135",
    "E136",
    "E137",
    "E138",
    "E139",
    "E140",
    "E141",
    "E142",
    "E144",
    "E145",
    "E146",
    "E150",
    "E383",
]
event_ok: list = [
    "R100",
    "R101",
    "R102",
    "R110",
    "R111",
    "R112",
    "R113",
    "R114",
    "R116",
    "R117",
    "R118",
    "R120",
    "R121",
    "R122",
    "R123",
    "R124",
    "R125",
    "R126",
    "R130",
    "R131",
    "R132",
    "R133",
    "R134",
    "R135",
    "R136",
    "R137",
    "R138",
    "R139",
    "R140",
    "R141",
    "R142",
    "R143",
    "R144",
    "R145",
    "R146",
    "R147",
    "R150",
    "R151",
    "R152",
    "R153",
    "R154",
    "R155",
    "R156",
    "R157",
    "R158",
    "R159",
    "R161",
    "R162",
    "R163",
    "R200",
    "R201",
    "R202",
    "R203",
    "R204",
    "R205",
    "R206",
    "R220",
    "R300",
    "R301",
    "R302",
    "R303",
    "R304",
    "R305",
    "R306",
    "R307",
    "R308",
    "R309",
    "R310",
    "R311",
    "R312",
    "R313",
    "R314",
    "R315",
    "R319",
    "R320",
    "R321",
    "R322",
    "R323",
    "R324",
    "R325",
    "R326",
    "R327",
    "R330",
    "R331",
    "R332",
    "R333",
    "R334",
    "R335",
    "R336",
    "R337",
    "R338",
    "R339",
    "R341",
    "R342",
    "R343",
    "R344",
    "R350",
    "R351",
    "R352",
    "R353",
    "R354",
    "R355",
    "R357",
    "R358",
    "R359",
    "R361",
    "R370",
    "R371",
    "R372",
    "R373",
    "R374",
    "R375",
    "R376",
    "R377",
    "R378",
    "R380",
    "R381",
    "R382",
    "R383",
    "R384",
    "R385",
    "R386",
    "R387",
    "R388",
    "R389",
    "R391",
    "R392",
    "R393",
    "R410",
    "R411",
    "R412",
    "R413",
    "R414",
    "R415",
    "R416",
    "R421",
    "R422",
    "R423",
    "R424",
    "R425",
    "R426",
    "R427",
    "R428",
    "R429",
    "R430",
    "R432",
    "R433",
    "R434",
    "R441",
    "R450",
    "R451",
    "R452",
    "R453",
    "R456",
    "R457",
    "R458",
    "R459",
    "R461",
    "R462",
    "R463",
    "R464",
    "R465",
    "R466",
    "R501",
    "R520",
    "R521",
    "R522",
    "R523",
    "R524",
    "R525",
    "R526",
    "R527",
    "R530",
    "R531",
    "R532",
    "R551",
    "R552",
    "R553",
    "R570",
    "R571",
    "R572",
    "R573",
    "R574",
    "R575",
    "R576",
    "R577",
    "R580",
    "R581",
    "R582",
    "R583",
    "R584",
    "R585",
    "R586",
    "R601",
    "R602",
    "R603",
    "R604",
    "R605",
    "R606",
    "R607",
    "R608",
    "R609",
    "R611",
    "R612",
    "R613",
    "R614",
    "R615",
    "R616",
    "R621",
    "R622",
    "R623",
    "R625",
    "R626",
    "R627",
    "R628",
    "R629",
    "R630",
    "R631",
    "R632",
    "R641",
    "R642",
    "R654",
    "R825",
    "R826",
]

other_events: list = [
    "E000",
    "E143",
    "E147",
    "E151",
    "E152",
    "E153",
    "E154",
    "E155",
    "E156",
    "E157",
    "E158",
    "E159",
    "E161",
    "E162",
    "E163",
    "E201",
    "E202",
    "E203",
    "E204",
    "E205",
    "E206",
    "E208",
    "E300",
    "E303",
    "E305",
    "E306",
    "E307",
    "E308",
    "E309",
    "E310",
    "E311",
    "E312",
    "E313",
    "E314",
    "E320",
    "E322",
    "E323",
    "E324",
    "E325",
    "E326",
    "E327",
    "E330",
    "E331",
    "E333",
    "E334",
    "E335",
    "E336",
    "E337",
    "E338",
    "E339",
    "E341",
    "E342",
    "E343",
    "E344",
    "E351",
    "E352",
    "E353",
    "E354",
    "E355",
    "E357",
    "E358",
    "E359",
    "E370",
    "E371",
    "E372",
    "E374",
    "E375",
    "E376",
    "E377",
    "E378",
    "E380",
    "E381",
    "E382",
    "E384",
    "E385",
    "E386",
    "E387",
    "E388",
    "E389",
    "E391",
    "E392",
    "E393",
    "E410",
    "E411",
    "E412",
    "E413",
    "E414",
    "E415",
    "E416",
    "E421",
    "E422",
    "E424",
    "E425",
    "E426",
    "E427",
    "E428",
    "E429",
    "E430",
    "E432",
    "E433",
    "E434",
    "E450",
    "E453",
    "E457",
    "E461",
    "E462",
    "E464",
    "E465",
    "E501",
    "E522",
    "E523",
    "E524",
    "E525",
    "E526",
    "E527",
    "E528",
    "E530",
    "E531",
    "E532",
    "E551",
    "E552",
    "E553",
    "E571",
    "E572",
    "E573",
    "E574",
    "E575",
    "E576",
    "E577",
    "E584",
    "E600",
    "E601",
    "E602",
    "E603",
    "E604",
    "E605",
    "E606",
    "E607",
    "E608",
    "E609",
    "E610",
    "E611",
    "E612",
    "E613",
    "E614",
    "E615",
    "E616",
    "E621",
    "E622",
    "E623",
    "E625",
    "E626",
    "E627",
    "E628",
    "E629",
    "E630",
    "E631",
    "E632",
    "E641",
    "E642",
    "E654",
    "E656",
    "E800",
    "E830",
]
