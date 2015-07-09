-- the description values for most of these actions is 'Referred'
SELECT description, COUNT(*)
FROM (
        SELECT bill_id, description, actor_id, legislator_id, committee_id, COUNT(*)
        FROM bills.bill_actions
        WHERE source_id = 2
        AND bill_id IS NOT NULL
        GROUP BY 1, 2, 3, 4, 5
        HAVING count(*) > 1
        ORDER BY 2
) as foo
GROUP BY 1
ORDER BY 2 DESC;
