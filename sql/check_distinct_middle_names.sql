-- shouldn't be more than one middle name with 2 or more characters for any combination of first, last and suffix
SELECT first_name, last_name, name_suffix, COUNT(DISTINCT middle_name)
FROM person_name
WHERE char_length(middle_name) >= 2
GROUP BY 1, 2, 3
HAVING COUNT(DISTINCT middle_name) > 1;