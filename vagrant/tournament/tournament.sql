-- Table definitions for the tournament project.
--
-- Put your SQL 'create table' statements in this file; also 'create view'
-- statements if you choose to use it.
--
-- You can write comments in this file by starting them with two dashes, like
-- these lines here.



CREATE TABLE players (id SERIAL primary key,
                      name TEXT);

CREATE TABLE matches (id SERIAL primary key,
                      winner INTEGER REFERENCES players (id),
                      loser INTEGER REFERENCES players (id));

CREATE VIEW win_total AS -- view shows players' total wins
                      (SELECT players.name as name, players.id as id,
                      count(matches.winner) AS win_total FROM players LEFT JOIN
                      matches ON players.id=matches.winner
                      GROUP BY players.id);

CREATE VIEW match_total AS -- view shows total matches played
                        (SELECT players.name as name, players.id as id,
                        count(matches.winner) AS match_total FROM players
                        LEFT JOIN matches ON (players.id=matches.winner OR
                        players.id=matches.loser) GROUP BY players.id);

CREATE VIEW standings AS -- view shows current player standings
                      (SELECT win_total.id, win_total.name, win_total, match_total
                      FROM (win_total JOIN match_total ON
                      win_total.id=match_total.id)) ORDER BY win_total DESC;
