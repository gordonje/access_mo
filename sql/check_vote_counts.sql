SELECT COUNT(*)
FROM (
        -- run from here to get distinct records 
        SELECT 
                  votes.id
                , votes.yes_count
                , yes_row_count
                , @(votes.yes_count - yes_row_count) as yes_diff
                , votes.no_count
                , no_row_count
                , @(votes.no_count - no_row_count) as no_diff
        FROM bills.votes
        JOIN (
                SELECT vote_id, COUNT(*) AS yes_row_count
                FROM bills.legislator_votes
                WHERE vote = 'yes'
                AND legislator_id IS NOT NULL
                GROUP BY vote_id
        ) AS y
        ON votes.id = y.vote_id
        JOIN (
                SELECT vote_id, COUNT(*) AS no_row_count
                FROM bills.legislator_votes
                WHERE vote = 'no'
                AND legislator_id IS NOT NULL
                GROUP BY vote_id
        ) AS n
        ON votes.id = n.vote_id
        WHERE (votes.yes_count <> yes_row_count
        OR votes.no_count <> no_row_count)
        AND source_id = 2
        ORDER BY 4 DESC, 7 DESC
        -- end here for distinct records
) AS foo;
