-- Dedupe Linda Black Fischer's record
UPDATE race_candidate
SET person_id = 220
WHERE person_id = 2081;

UPDATE person_name
SET person_id = 220
WHERE person_id = 2081;

DELETE
FROM person
WHERE id NOT IN (SELECT person_id FROM person_name);

-- Add Lana Ladd Baker's record
UPDATE person
SET middle_name = '', last_name = 'Ladd Baker'
WHERE middle_name = 'Ladd';

INSERT INTO person_name (person_id, first_name, middle_name, last_name, name_suffix, nickname, created_date)
SELECT id as person_id, first_name, middle_name, last_name, name_suffix, '', now() as create_date
FROM person
WHERE last_name = 'Ladd Baker';