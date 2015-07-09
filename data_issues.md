# Data Issues #

This document describes problems found in the current version of Access Missouri's development database. It also includes possible remedies.

---------------------------------------

## Duplicate bill_actions ##

### Symptoms ###

As of July 7, 2015, [three-quarters of the bills](https://github.com/gordonje/access_mo/blob/master/sql/pct_bills_w_dupe_actions.sql) in the db have duplicate bill_actions.

By duplicate, we mean that the same bill has the same description for the same actor (e.g., "Senate", "House" "Governor"). However, these duplicates may have differing action_date values. Given this definition, bills currently have as many as 16 duplicate actions. 

Among the [most egregious examples](https://github.com/gordonje/access_mo/blob/master/sql/bills_w_most_dupes.sql) is SB 493 from the 2014 Regular Session (bill_id = 26513), which has 106 duplicate actions. End users can even see these duplication actions on the [bill's profile](http://dev.accessmissouri.org/bills/profile.php?id=26513) (note that the problem is not yet on the [production site](http://www.accessmissouri.org/bills/profile.php?id=26513)), so solving this problem is critical to releasing the new version of the database.

### Diagnosis ###

About [86 percent](https://github.com/gordonje/access_mo/blob/master/sql/bill_actions_sources.sql) of bill_actions are sourced to the Open States API. The rest are sourced to 'Access Missouri' and are associated with a specific house or senate journal. Even when filtering to one source or the other, duplicate bill_actions are found.

While most of the duplicate bill_actions are sourced to Open States, these duplicate are not coming from Open States. For example, when [calling Open States' bill details method](https://github.com/gordonje/access_mo/blob/master/openstates_api/test_api.py) (documentation available [here](http://sunlightlabs.github.io/openstates-api/bills.html#methods/bill-detail)) for the SB 493 from the 2014 Regular Session, the [results](https://github.com/gordonje/access_mo/blob/master/openstates_api/results.csv) include 110 actions as opposed to the 218 bill_actions currently in the db for bill_id 26513.

Some of duplicates that meet the above criteria are legitimately distinct bill_actions. For example, see [HB 1439](http://openstates.org/api/v1/bills/MOB00004090/?apikey=3f2d045c8820407ebcac7c212ec19387) from the 2014 Regular Session (bill_id 25520) wherein you'll finds multiple 'House Message (H)' and 'Senate Message (S)' actions within days of each other, as opposed to hours of each other.

The interval between action_date values of the seemingly dupe records may be the key to identifying which are actual dupes. For the groups of duplicates sourced to Open States, [98 percent](https://github.com/gordonje/access_mo/blob/master/sql/os_dupes_w_durations.sql) have a duration of 5 to 6 hours between the earliest and most recent action_dates.

Another clue is that all of the action_dates values are timestamped at 6 pm, 7 pm and midnight, the latter being a default value. Also, if you [download](http://openstates.org/downloads/) Missouri's complete set of bill_actions from Open States, you'll see that all of the datetime values are set to midnight. Seems as though these time values are being added by us somewhere.

The bill_actions sourced to Access Missouri are all timestamped at 6 or 7 pm (there are 741 with NULL values). The [description values](https://github.com/gordonje/access_mo/blob/master/sql/am_dupe_desc.sql) for most of these bill_actions are is 'Referred'. Others include 'Adopted', 'Signed, Delivered' and 'Governor Veto'.

Looking back at the journals from which these actions were extracted, we find that for a given bill, the same action can appear on different journal dates. This is where the problem gets stickier. 

In some cases, these legitimately distinct actions, but we are missing necessary info. For example, see [SB 373](http://www.accessmissouri.org/bills/profile.php?id=28907) from the 2015 Regular Session (bill_id 28907), which was 'Referred' on Feb. 24 and again on April Apr. 28. Looking in the associated Senate Journals, it seems that this bill was referred to the 'Transportation, Infrastructure and Public Safety' committee [on Feb. 24](http://www.senate.mo.gov/15info/Journals/RDay260224417-433.pdf#toolbar=1) and on [Apr. 28](http://www.senate.mo.gov/15info/Journals/RDay5904281103-1166.pdf#toolbar=1)(search for SB 373) a floor substitution was made and the bill was referred to the 'Committee on Governmental Accountability and Fiscal Oversight'. The committee_id associated with each of these actions is NULL.

It's also possible that the front-end code on the development server is also contributing to a display of duplicates bill actions. See the dev site version of [SB 373](http://dev.accessmissouri.org/bills/profile.php?id=28907) and you'll note that, for example, it is marked as 'Introduced, 1st Read', but in the db, bill_id 28907 has only one bill_action with this description value.

While the above case is an example of legitimately distinct bill_actions found in the journals, other the legitimacy of other duplicate examples from this source is questionable. For example, look at [SB 182](http://dev.accessmissouri.org/bills/profile.php?id=24681) from the 2013 Regular Session (bill_id 24681), which was marked as vetoed 16 times (interestingly, these duplicates are also found on the [live site](http://www.accessmissouri.org/bills/profile.php?id=24681), though again, they are not coming from [Open States](http://openstates.org/api/v1/bills/MOB00002186/?apikey=3f2d045c8820407ebcac7c212ec19387)). 

If you look at the senate journals associate with these actions, you'll find that on every weekday between [Apr. 23](http://www.senate.mo.gov/13info/Journals/RDay540422823-850.pdf#toolbar=1) and [May 17](http://www.senate.mo.gov/13info/Journals/RDay6905161967-2334.pdf#toolbar=1), the bill is listed on the senate formal calendar as having been vetoed.

### Open questions ###

Where are the 6 pm and 7 pm time action_date values coming from?

Why are certain bill actions, like the governor's vetoing of a bill, repeated multiple times in the journals?

### Possible Remedies ###

We can prevent these and similar issues by defining and implementing more precise data definitions. Specifically, we might consider re-casting the action_date column from timestamp to a date column because it isn't clear that we are ever going to be provide with the specific times that these action happen. And if action_date were a date field, we can implement a unique constraint on combinations of bill_id, description, action_date and actor_id.

Thus, explicit errors will be raised when we violate a constraint, and we can catch when those errors are raised.

More generally, we might consider whether its worth the effort to gather bill_actions is data from the journals. What can we get from the journals that we can't get from the Open States or crawling the House and Senate clerk sites? Whatever it is, we might consider focusing specifically on getting that info.

In either case, we should consider adding date_created column to bill_actions (actually, probably to every table) with a not null constraint and a default set to the current time. This should make troubleshooting these records a little easier.

## Missing bill_ids for bill_actions ##

### Symptoms ###

As of July 7, 2015, there are 332 bill_actions records where the bill_id is NULL, which is contrary to our working definition of a bill_action. While this is not an error that will be obvious to end users, it could be a symptom of a broader problem in our data collection processes.

### Diagnosis ###

Speculating, but maybe these are just old bad records that need to be deleted. Or maybe somewhere there's an import process inserting bill_actions without properly associating them with bills. 

### Possible Remedies ###

If we had a not null or foreign key constraint here, we'ld know when the error is raised and could then know when and where to address it.