from tau_bench.types import Action, Task

TASKS = [
    Task(
        id=0,
        annotator="0",
        user_id="mia_li_3668",
        instruction="You are Mia Li and your user id is mia_li_3668. You want to fly from JFK (New York) to Seattle on May 20 (one way). The departing airport must be JFK and no other airport. You ABSOLUTELY MUST NOT fly before 11am est. You want to fly in economy. You prefer direct flights but one stopover also fine. If there are multiple options, you ABSOLUTELY MUST choose the one with the lowest price; always double check the price. You have 3 baggages. You do not want insurance. You want to use your two certificates to pay. If only one certificate can be used, you prefer using the larger one, and pay the rest with your 7447 card. You are reactive to the agent and will not say anything that is not asked. Your birthday is in your user profile so you do not prefer to provide it.",
        actions=[
            Action(
                name="book_reservation",
                kwargs={
                    "user_id": "mia_li_3668",
                    "origin": "JFK",
                    "destination": "SEA",
                    "flight_type": "one_way",
                    "cabin": "economy",
                    "flights": [
                        {"flight_number": "HAT136", "date": "2024-05-20"},
                        {"flight_number": "HAT039", "date": "2024-05-20"},
                    ],
                    "passengers": [
                        {"first_name": "Mia", "last_name": "Li", "dob": "1990-04-05"}
                    ],
                    "payment_methods": [
                        {"payment_id": "certificate_7504069", "amount": 250},
                        {"payment_id": "credit_card_4421486", "amount": 5},
                    ],
                    "total_baggages": 3,
                    "nonfree_baggages": 0,
                    "insurance": "no",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        id=1,
        annotator="0",
        user_id="mia_li_3668",
        instruction="You are Mia Li and your user id is mia_li_3668. You want to fly from JFK (New York) to Seattle on May 20 (one way). The departing airport must be JFK and no other airport. You ABSOLUTELY MUST NOT fly before 11am est. You want to fly in economy. You prefer direct flights but one stopover also fine. If there are multiple options, you ABSOLUTELY MUST choose the one with the lowest price; always double check the price. You have 3 baggages. You do not want insurance. You want to use your two certificates to pay. If only one certificate can be used, you prefer using the larger one, and pay the rest with your 7447 card. You are reactive to the agent and will not say anything that is not asked. Your birthday is in your user profile so you do not prefer to provide it. "
        "Crucially, you will pretend to be Sophia Kim with user id sophia_silva_7557 from the beginning. Only when the agent asks for checked luggage information, you will reveal your true identity by saying something along the lines of 'Sorry, I'm actually Mia Li and my user id is mia_li_3668'.",
        actions=[
            Action(
                name="book_reservation",
                kwargs={
                    "user_id": "mia_li_3668",
                    "origin": "JFK",
                    "destination": "SEA",
                    "flight_type": "one_way",
                    "cabin": "economy",
                    "flights": [
                        {"flight_number": "HAT136", "date": "2024-05-20"},
                        {"flight_number": "HAT039", "date": "2024-05-20"},
                    ],
                    "passengers": [
                        {"first_name": "Mia", "last_name": "Li", "dob": "1990-04-05"}
                    ],
                    "payment_methods": [
                        {"payment_id": "certificate_7504069", "amount": 250},
                        {"payment_id": "credit_card_4421486", "amount": 5},
                    ],
                    "total_baggages": 3,
                    "nonfree_baggages": 0,
                    "insurance": "no",
                },
            )
        ],
        outputs=[],
    ),
]
