-- update the person_id of the race_candidate records to the id of the person with both the first and middle name
UPDATE race_candidate
SET person_id = a.id
FROM person a
JOIN person b
ON a.middle_name = b.first_name
AND a.last_name = b.last_name
AND a.name_suffix = b.name_suffix
WHERE race_candidate.person_id = b.id
AND a.id <> b.id;

-- update the person_id of the person records to the id of the person with both the first and middle name
UPDATE person_name
SET person_id = a.id
FROM person a
WHERE a.middle_name = person_name.first_name
AND a.last_name = person_name.last_name
AND a.name_suffix = person_name.name_suffix
AND a.id <> person_name.person_id;

-- make sure Gail McCann Beatty's person record has her full name
UPDATE person
SET last_name = 'McCann Beatty'
WHERE first_name = 'E'
AND middle_name = 'Gail'
AND last_name = 'Beatty';

-- delete any person records without any person_name records
DELETE
FROM person
WHERE id NOT IN (SELECT person_id FROM person_name);
