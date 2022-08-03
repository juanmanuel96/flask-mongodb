FINAL = 'FINAL'
RELEASE_CANDIDATE = 'RC'
VALID_STATES = [FINAL, 'ALPHA', 'BETA', RELEASE_CANDIDATE]


def get_version(version_info: tuple) -> str:
    version_number: tuple[int] = version_info[:3]  # First three numbers are the MAJOR, MINOR, and PATCH
    version_state: str = version_info[3]  # Package state
    state_number: int = version_info[4]  # State number
    version = '.'.join([str(v) for v in version_number])
    
    if version_state.upper() not in VALID_STATES:
        # TODO Need specific Exception for this
        raise Exception('Not a valid package state')
    if version_state.upper() == FINAL:
        return version
    if RELEASE_CANDIDATE in version_state.upper():
        return version + f'-{version_state}'
    version += f'-{version_state}.{state_number}'
    return version
