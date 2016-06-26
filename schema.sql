drop table if exists cities;
create table cities (
    id integer unique,
    city text not null,
    country_code text not null collate nocase,
    lon real not null,
    lat real not null
);