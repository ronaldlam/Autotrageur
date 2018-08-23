import schedule


class NonUniqueJobTagError(Exception):
    """Exception thrown when unique jobs were expected but not observed."""
    pass


def fetch_jobs(tag=None):
    """Fetch list of jobs with given tag, all jobs if no tag specified.

    Args:
        tag (str, optional): Defaults to None. The tag to look up.

    Returns:
        list(schedule.Job): The list of jobs.
    """
    if tag is None:
        return schedule.jobs
    else:
        return [job for job in schedule.jobs if tag in job.tags]


def fetch_only_job(tag):
    """Fetch a single job with the given tag.

    Args:
        tag (str): The tag to look up.

    Raises:
        NonUniqueJobTagError: If the single job was not found or was
            non-unique.

    Returns:
        schedule.Job: The single job.
    """
    job_list = fetch_jobs(tag)

    if len(job_list) != 1:
        raise NonUniqueJobTagError('Jobs found: {}'.format(job_list))
    else:
        return job_list[0]
