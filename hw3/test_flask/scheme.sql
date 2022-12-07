create table entries (
    id integer primary key autoincrement,
    text text not null,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    author text not null
);

create table users (
    id integer primary key autoincrement,
    username text not null,
    password text not null
);

create table forms(
    id integer primary key autoincrement,
    user text not null,
    first_name text,
    last_name,
    date_of_birth DATE,
    email text,
    education text,
    skills text,
    favourite_color text
);