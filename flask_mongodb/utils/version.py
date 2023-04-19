import typing as t

FINAL = 'FINAL'
RELEASE_CANDIDATE = 'RC'
DEVELOPMENT = ('DEV', 'DEVELOPMENT')
VALID_STATES = [FINAL, 'ALPHA', 'BETA', RELEASE_CANDIDATE, *DEVELOPMENT]


def get_version(version_info: t.Tuple[int, int, int, str,  int]) -> str:
    version_number: tuple[int] = version_info[:3]  # First three numbers are the MAJOR, MINOR, and PATCH
    version_state: str = version_info[3]  # Package state
    state_number: int = version_info[4]  # State number
    version = '.'.join([str(v) for v in version_number])
    
    if version_state.upper() not in VALID_STATES:
        # TODO Need specific Exception for this
        raise Exception('Not a valid package state')
    if version_state.upper() == FINAL:
        return version
    if version_state.upper() == RELEASE_CANDIDATE:
        return version + f'-{version_state}{state_number}'
    version += f'-{version_state}{state_number}'
    return version
