from dataclasses import dataclass


@dataclass
class Form:
    first_name: str
    last_name: str
    date_of_birth: str
    email: str
    education: str
    skills: str
    favourite_color: str
