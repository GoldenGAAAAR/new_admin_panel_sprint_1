CREATE SCHEMA content;

CREATE EXTENSION "uuid-ossp";

CREATE TABLE IF NOT EXISTS content.film_work (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    description TEXT,
    creation_date DATE,
    rating FLOAT,
    type TEXT NOT NULL,
    created TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    modified TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS content.genre (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT,
    created TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    modified TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS content.person (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name TEXT NOT NULL,
    created TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    modified TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS content.genre_film_work (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    genre_id UUID NOT NULL REFERENCES content.genre (id) ON DELETE CASCADE,
    film_work_id UUID NOT NULL REFERENCES content.film_work (id) ON DELETE CASCADE,
    created TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS content.person_film_work (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    person_id UUID NOT NULL REFERENCES content.person (id) ON DELETE CASCADE,
    film_work_id UUID NOT NULL REFERENCES content.film_work (id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    created TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE UNIQUE INDEX genre_name_key ON content.genre (name);

CREATE UNIQUE INDEX film_work_title_key ON content.film_work (title);

CREATE UNIQUE INDEX person_full_name_key ON content.person (full_name);

CREATE UNIQUE INDEX genre_film_work_genre_id_film_work_id_key ON content.genre_film_work (genre_id, film_work_id);

CREATE UNIQUE INDEX person_film_work_person_id_film_work_id_key ON content.person_film_work (person_id, film_work_id);
