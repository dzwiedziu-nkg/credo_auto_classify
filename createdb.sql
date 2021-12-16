CREATE TABLE classes (
    id_class SERIAL PRIMARY KEY,
    class_name VARCHAR(255) NOT NULL UNIQUE,
    class_symbol VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE classifier_types (
    id_classifier_type SERIAL PRIMARY KEY,
    classifier_type_name VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE classifiers (
    id_classifier SERIAL PRIMARY KEY,
    id_classifier_type INT NOT NULL REFERENCES classifier_types(id_classifier_type),
    classifier_name VARCHAR(255) NOT NULL UNIQUE,
    classifier_symbol VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE images (
    id BIGINT PRIMARY KEY,
    timestamp BIGINT,
    time_received BIGINT,
    source VARCHAR(255),
    visible BOOLEAN,

    device_id INT,
    user_id INT,
    team_id INT,

    accuracy DOUBLE PRECISION,
    altitude DOUBLE PRECISION,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    provider VARCHAR(255),

    frame_content TEXT,
    height SMALLINT,
    width SMALLINT,
    x SMALLINT,
    y SMALLINT,

    metadata_max SMALLINT,
    metadata_average DOUBLE PRECISION,
    metadata_blacks DOUBLE PRECISION,
    metadata_black_threshold SMALLINT,
    metadata_ax DOUBLE PRECISION,
    metadata_ay DOUBLE PRECISION,
    metadata_az DOUBLE PRECISION,
    metadata_orientation DOUBLE PRECISION,
    metadata_temperature SMALLINT,

    ml_score DOUBLE PRECISION
);

CREATE TABLE classifications (
    id BIGINT NOT NULL REFERENCES images(id),
    id_classifier INT NOT NULL REFERENCES classifiers(id_classifier),
    id_class INT NOT NULL REFERENCES classes(id_class)
);
