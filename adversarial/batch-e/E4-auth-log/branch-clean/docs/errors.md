# Error contract (normative for this fixture)

A denied request returns the identical status and body whether or not the job id
exists, and reads no job content in the process. Logging must never change
what a denied caller observes.
