-- fill in nicknames on distinct person records
UPDATE person
SET nickname = person_name.nickname
FROM person_name
WHERE person.id = person_name.person_id
AND person_name.nickname <> ''; 