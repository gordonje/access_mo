-- Set the rank value
UPDATE public.race_candidate
SET rank = a.the_rank 
FROM (
	SELECT 
                  race_candidate.id
                , rank() OVER (PARTITION BY race_id ORDER BY votes DESC) as the_rank
	FROM race_candidate
) as a
WHERE a.id = race_candidate.id;



