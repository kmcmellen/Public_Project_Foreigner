Sandy Springs Minutes Agent - Project Foreigner README - THIS PROJECT IS IN DEVELOPMENT

Disclaimer:
Scripts, software, instructions, all files under this repository are provided on an "as-is" basis, without warranty.  Use is at your own risk.  No support or maintenance is guaranteed.
Use of this software/solution does not imply endorsement by the City of Sandy Springs.  A LICENSE file is included in the repository.

Note:
The name "Project Foreigner" is a nod to the Gen X creator/author of this project and is meant to be humorous.  The band Foreigner's 1984 album "Agent Provocateur" is where the name 
comes from, as this project is about agentic AI.  Secondarily, this project is also about being a "provocateur" of innovation, also using the term in a humorous way.  

Purpose:
The City of Sandy Springs is using City Council meeting transcripts, agendas, leveraging AI to draft meeting minutes as an initial use case of agentic AI.  This is currently a manual
process.  Once successful, expanded use will possibly include Development Authority meetings, Work Sessions, and/or Budget Workshops.  

Data Sources:
1. Sandy Springs live streams their Council Meetings on YouTube.  They exist here:  https://www.youtube.com/@CityOfSandySprings/streams
2. Public Meetings, dates, agendas, packets, etc., are in CivicClerk.  Those reside here:  https://sandyspringsga.portal.civicclerk.com/
3. Assistant Instructions.docx: Formatting rules, general AI instructions, how to treat agenda items, what to do if information is missing.
4. Reference File for Minutes.xlsx: Names of Mayor, Councilmembers, Department Heads, Points of Interest. This is used to resolve potential misspellings, or provide context.

Data Source Notes:
Early testing noted that AI would skip later agenda items from the draft minutes unless an agenda file was included. Also, the agenda file was needed for the consent agenda.  The minutes
provided by the City Clerk's office included an item name for the consent agenda, although they were not officially read in into the transcript during the meeting.  Having the agenda file
and including it in the instruction set resolved this issue.  The Reference File provides necessary context.  For example, Councilwoman Mular's name is often transcribed as "Councilwoman Mueller" by YouTube". 
By including the correct spelling and noting it in the Assistant Instructions, this will override the transcript's incorrect spelling.  Further details in the Assistant Instructions exist 
to protect from hallucinations or a lack of clarity in the transcript by inserting "[VERIFY]" to call attention to potential issues.

Pre-Implementation Requirements:
The YouTube transcript can be downloaded manually.  To download the transcript via the agent, an API key, OAuth ClientID and OAuth client secret will need to be generated from the Google Cloud Platform. 
Your City's YouTube Channel ID is also needed.  These values are part of a one-time setup process and will reside in your client_secrets.json that is part of .gitignore, for security reasons.  The 
authenticate.py script completes this setup. 

Working Scripts:
1. download_captions.py
Functions to return a list of candidate meeting based on the recent list and select the most recent one that meets the criteria of being a Council Meeting.     
   
2. run_latest_transcript.py
Wrapper script for download_captions, outputs to a file with the name "transcript_YYYY_MM_DD.txt"

3. get_latest_council_agenda.py
Retrieves the latest Council Meeting after reading the calendar in CivicClerk.  Note: CivicClerk paginates calendar list items.  You may have to add into an OAuth pagination line into your script in
order to find the correct item.  (That was done here.) 

4. run_latest_agenda.py
Wrapper script for get_latest_council_agenda.  This returns a JSON file with the name of "civicclerk_agenda_MMDDYYYY.json".  The file contains the metadata and URL of the agenda in CivicClerk which is used
by AI for minutes generation.



