-- Insert assembly member records for winning race candidates
INSERT INTO assembly_member (
          assembly_id
        , person_id
        , chamber_id
        , district
        , party
        , counties
        , race_candidate_id
        , source_doc_id
        , created_date
)
SELECT 
          election.assembly_id
        , race_candidate.person_id
        , CASE 
                WHEN race_type.name = 'State Senator' THEN 'S'
                WHEN race_type.name = 'State Representative' THEN 'H'
          END as chamber_id
        , race.district
        , NULL as party
        , NULL as counties
        , race_candidate.id
        , NULL as source_doc
        , now() as created_date
FROM race_candidate
JOIN race
ON race_id = race.id
JOIN race_type
ON race_type_id = race_type.id
JOIN election
ON election_id = election.id
WHERE rank = 1
AND election.assembly_id IS NOT NULL;

-- since senators serve four years, insert records for their second assembly
INSERT INTO assembly_member (
          assembly_id
        , person_id
        , chamber_id
        , district
        , party
        , counties
        , race_candidate_id
        , source_doc_id
        , created_date
)
SELECT 
          assembly_member.assembly_id + 1 as assembly_id
        , assembly_member.person_id
        , assembly_member.chamber_id
        , assembly_member.district
        , NULL as party
        , NULL as counties
        , assembly_member.race_candidate_id
        , NULL as source_doc
        , now() as created_date
FROM assembly_member
JOIN race_candidate
ON race_candidate.id = race_candidate_id
JOIN race
ON race.id = race_id
JOIN election 
ON election.id = election_id
JOIN election_type
ON election_type_id = election_type.id
WHERE chamber_id = 'S'
-- exclude this one guy who was elected by special session, then re-elected in the next general
AND election_type.name <> 'Special';